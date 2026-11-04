import argparse
from collections import Counter, defaultdict, deque
from contextlib import ExitStack
from datetime import UTC, datetime
import hashlib
import json
import mimetypes
from pathlib import Path
import re
import time
from urllib.parse import unquote, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
import httpx

from browser import Browser, VerificationRequired, challenge
from discovery import PRIVATE, extension, host, is_document, normalize
from sources import SOURCES

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "data-sources-scraping.jsonl"
OUTPUT = ROOT / "data/input"
PRIVATE_DIR = ROOT / ".scraping"
AGENT = "ElixirAtlas/0.1 (public research corpus)"


class Collector:
    def __init__(self, stack, index, output, delay, max_bytes, headed,
                 browser_state=PRIVATE_DIR / "browser-state.json", cookies=None,
                 verification_timeout=0, browser_channel="chrome", refresh=False):
        self.index, self.output = index, output
        self.delay, self.max_bytes, self.headed, self.refresh = delay, max_bytes, headed, refresh
        self.stack = stack
        self.client = stack.enter_context(httpx.Client(follow_redirects=True, timeout=45, headers={"User-Agent": AGENT}))
        self.cache, self.latest = {}, {}
        if index.exists():

            with index.open("rb+") as f:
                lines = f.readlines()
                offset = 0
                for position, line in enumerate(lines):
                    try:
                        self.remember(json.loads(line))
                    except json.JSONDecodeError:
                        if position != len(lines) - 1 or line.endswith(b"\n"):
                            raise ValueError(f"Invalid index line {position + 1}; refusing to discard history")
                        f.truncate(offset)
                        print("Recovered an interrupted final index entry.", flush=True)
                        break
                    offset += len(line)
                else:
                    if lines and not lines[-1].endswith(b"\n"):
                        f.write(b"\n")
        self.browser = None
        self.browser_state, self.cookies, self.verification_timeout = browser_state, cookies, verification_timeout
        self.browser_channel = browser_channel
        self.robots = {}
        self.blocked_hosts = set()
        self.last_request = 0

    def remember(self, row):
        key = row["source"], row.get("url")
        self.latest[key] = row
        if row["status"] == "saved":
            self.cache[key] = row
        elif row["status"] in ("excluded", "failed", "blocked", "skipped", "pending"):
            self.cache.pop(key, None)

    def record(self, source, url, status, **details):
        previous = self.latest.get((source, url), {})
        row = {"source": source, "url": url, "status": status, **details}
        comparable = lambda item: {k: v for k, v in item.items() if k != "updated_at"}
        if comparable(row) == comparable(previous):
            return previous
        row["updated_at"] = datetime.now(UTC).isoformat(timespec="seconds")
        self.index.parent.mkdir(parents=True, exist_ok=True)
        with self.index.open("a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.remember(row)
        return row

    def discovered(self, source, row, status, **details):
        metadata = {k: v for k, v in row.items() if k not in ("source", "url", "status", "updated_at", "discovery_status", "discovery_error", "links")}
        return self.record(source, row["url"], "saved", **metadata, discovery_status=status, **details)

    def pause(self):
        time.sleep(max(0, self.delay - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()

    def browser_fetch(self, url, source):
        if self.browser is None:
            self.browser = Browser(self.stack, self.browser_state, self.cookies, self.headed, self.verification_timeout, self.browser_channel)
        return self.browser.fetch(url, is_document(url), self.max_bytes,
                                  lambda reason: self.record(source, url, "blocked", reason=reason))

    def request(self, url, browser=False, source=None):
        self.pause()
        if browser:
            return self.browser_fetch(url, source)
        for attempt in range(3):
            with self.client.stream("GET", url) as response:
                if response.status_code in (429, 502, 503, 504) and attempt < 2:
                    retry = response.headers.get("retry-after", "")
                    time.sleep(min(float(retry), 30) if retry.isdigit() else 2 ** (attempt + 1))
                    continue
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > self.max_bytes:
                        raise ValueError(f"File exceeds {self.max_bytes // (1024 * 1024)} MiB limit")
                content_type = response.headers.get("content-type", "").split(";")[0]
                if "html" in content_type and challenge(bytes(body), response.headers):
                    return self.browser_fetch(url, source)
                response.raise_for_status()
                return bytes(body), str(response.url), content_type, "response"

    def permitted(self, url):
        if host(url) == "zenodo.org" and urlsplit(url).path.startswith("/api/records"):
            return True
        origin = urlunsplit((*urlsplit(url)[:2], "", "", ""))
        if origin not in self.robots:
            self.pause()
            response = self.client.get(origin + "/robots.txt")
            rules = RobotFileParser()
            rules.parse(response.text.splitlines() if response.status_code == 200 and "<html" not in response.text.lower() else [])
            self.robots[origin] = rules
        return self.robots[origin].can_fetch(AGENT, url)

    def save(self, source, url, body, final_url, content_type, representation, discovered_from=None):
        if len(body) > self.max_bytes or not body:
            raise ValueError("Empty response or download exceeds size limit")
        if "html" in content_type:
            soup = BeautifulSoup(body, "html.parser")
            title = soup.title.get_text(strip=True) if soup.title else ""
            if challenge(body) or soup.select_one("#block-elixir2-accessdeniedanonymous") or title.lower() == "access denied" or PRIVATE.search(urlsplit(final_url).path):
                raise ValueError("Blocked or redirected to a login page")
            if is_document(url):
                raise ValueError("Expected a document, received HTML")
        suffix = extension(final_url)
        if "html" in content_type:
            suffix = ".html"
        elif "json" in content_type:
            json.loads(body)
            suffix = ".json"
        elif "pdf" in content_type or body.startswith(b"%PDF"):
            if not body.startswith(b"%PDF"):
                raise ValueError("Response claims PDF but has no PDF signature")
            suffix = ".pdf"
        elif not re.fullmatch(r"\.[a-zA-Z0-9]{1,10}", suffix):
            suffix = mimetypes.guess_extension(content_type) or ".bin"
        stem = re.sub(r"[^A-Za-z0-9._-]+", "-", unquote(urlsplit(url).path).strip("/"))[-90:].lstrip(".") or "index"
        path = self.output / source / f"{stem}-{hashlib.sha256(url.encode()).hexdigest()[:12]}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.part")
        temporary.write_bytes(body)
        temporary.replace(path)
        return self.record(source, url, "saved", final_url=final_url,
                           path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                           content_type=content_type, bytes=len(body), representation=representation,
                           retrieved_at=datetime.now(UTC).isoformat(timespec="seconds"),
                           discovered_from=discovered_from, discovery_status="pending")

    def fetch(self, source, url, browser=False, discovered_from=None):
        cached = self.cache.get((source, url))
        if cached and not self.refresh:
            path = ROOT / cached["path"]
            if path.is_file() and path.stat().st_size == cached["bytes"]:
                if discovered_from and not cached.get("discovered_from"):
                    cached = {**cached, "discovered_from": discovered_from}
                return path.read_bytes(), cached, True
        try:
            if host(url) in self.blocked_hosts:
                self.record(source, url, "blocked", reason="This host needs manual verification; rerun to retry", discovered_from=discovered_from)
                return None
            if not self.permitted(url):
                self.record(source, url, "skipped", reason="Disallowed by robots.txt", discovered_from=discovered_from)
                return None
            body, final_url, content_type, representation = self.request(url, browser, source)
            row = self.save(source, url, body, final_url, content_type, representation, discovered_from)
            return body, row, False
        except (httpx.HTTPError, ValueError, OSError) as error:
            self.record(source, url, "failed", error=str(error)[:500], discovered_from=discovered_from)
            print(f"[{source}] failed {url}: {error}", flush=True)
            return None


def collect(collector, name, source, max_pages=0):
    if source.deferred:
        for url in source.urls or (None,):
            collector.record(name, normalize(url) if url else None, "deferred", reason=source.deferred, sections=source.sections)
        print(f"[{name}] deferred: {source.deferred}", flush=True)
        return True
    queue, queued = deque(), set()
    counts, ids, totals, occurrences = Counter(), defaultdict(set), defaultdict(set), Counter()

    def enqueue(url, action="download", parent=None):
        url = normalize(url)
        if not url or url in queued:
            return
        queued.add(url)
        if action != "download":
            reason = "Video processing deferred" if action == "video" else "Attachment format excluded by source policy"
            collector.record(name, url, "deferred", reason=reason, discovered_from=parent)
            counts["deferred"] += 1
            return
        if (name, url) not in collector.latest:
            collector.record(name, url, "pending", discovered_from=parent)
        queue.append((url, parent))

    for url in source.urls:
        enqueue(url)
    stopped = False
    try:
        while queue and (not max_pages or counts["visited"] < max_pages):
            url, parent = queue.popleft()
            counts["visited"] += 1
            try:
                use_browser = source.browser and host(url) == host(source.urls[0])
                result = collector.fetch(name, url, use_browser, parent)
            except VerificationRequired as error:
                collector.record(name, url, "blocked", reason=str(error), discovered_from=parent)
                collector.blocked_hosts.add(host(url))
                counts["blocked"] += 1
                print(f"[{name}] paused: {url}: {error}", flush=True)
                stopped = True
                continue
            if result is None:
                counts["failed_or_skipped"] += 1
                continue
            body, row, cached = result
            counts["cached" if cached else "saved"] += 1
            try:
                found = source.discover(body, row["final_url"], row["content_type"], source)
                for child, action in found.links:
                    enqueue(child, action, url)
                if found.group:
                    ids[found.group].update(found.ids)
                    occurrences[found.group] += len(found.ids)
                    if found.total is not None:
                        totals[found.group].add(found.total)
                collector.discovered(name, row, "complete", links=len(found.links))
            except (KeyError, TypeError, ValueError) as error:
                collector.discovered(name, row, "failed", discovery_error=str(error)[:500])
                counts["discovery_failed"] += 1
                print(f"[{name}] discovery failed {url}: {error}", flush=True)
            if counts["visited"] % 100 == 0:
                print(f"[{name}] {dict(counts)}, queued={len(queue)}", flush=True)
    except KeyboardInterrupt:
        collector.record(name, None, "interrupted", counts=dict(counts), remaining=len(queue) + 1)
        raise
    checks = {}
    for group in ids.keys() | totals.keys():
        expected = sorted(totals[group])
        duplicates = occurrences[group] - len(ids[group])
        matched = len(expected) == 1 and len(ids[group]) == expected[0] and not duplicates
        checks[group] = {"unique_records": len(ids[group]), "reported_totals": expected,
                         "duplicates": duplicates, "matched": matched}
    incomplete = stopped or bool(queue) or any(counts[k] for k in ("failed_or_skipped", "discovery_failed")) or any(not c["matched"] for c in checks.values())
    status = "incomplete" if incomplete else "collected"
    collector.record(name, None, status, counts=dict(counts), remaining=len(queue), catalogues=checks,
                     sections=source.sections, note="Coverage is limited to configured seeds and discovered links.")
    print(f"[{name}] {status}: {dict(counts)}, remaining={len(queue)}, catalogues={checks}", flush=True)
    return incomplete


def main():
    parser = argparse.ArgumentParser(description="Collect raw sources; rerun to resume.")
    parser.add_argument("sources", nargs="*", help="Source names or all; omit to list")
    parser.add_argument("--refresh", action="store_true", help="Fetch selected sources again instead of reusing saved responses")
    parser.add_argument("--max-pages", type=int, default=0, help="Per-source smoke-test limit; 0 collects all discovered URLs")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between requests")
    parser.add_argument("--max-mb", type=int, default=100, help="Maximum size of one download")
    parser.add_argument("--headed", action="store_true", default=True, help="Show the browser for manual checks (default)")
    parser.add_argument("--headless", action="store_false", dest="headed", help="Stop the source if a manual browser check is needed")
    parser.add_argument("--cookies", type=Path, help="Import your JSON cookies or Playwright storage state before navigation")
    parser.add_argument("--browser-channel", default="chrome", choices=("chrome", "chromium", "msedge"))
    parser.add_argument("--browser-state", type=Path, default=PRIVATE_DIR / "browser-state.json")
    parser.add_argument("--verification-timeout", type=float, default=0, help="Manual verification wait; 0 waits until completed or interrupted")
    parser.add_argument("--index", type=Path, default=INDEX)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--import-file", type=Path, help="Import a raw Browser download for one source and --url")
    parser.add_argument("--url", help="Original URL of the manually downloaded file")
    parser.add_argument("--content-type", help="Override the imported file's MIME type")
    args = parser.parse_args()
    if not args.sources:
        for name, source in SOURCES.items():
            print(f"{name}: sections {','.join(map(str, source.sections))}; {source.deferred or ', '.join(source.urls)}")
        return
    names = list(SOURCES) if args.sources == ["all"] else list(dict.fromkeys(args.sources))
    if set(names) - SOURCES.keys():
        parser.error("Unknown sources: " + ", ".join(set(names) - SOURCES.keys()))
    if args.delay < 0 or args.max_pages < 0 or args.max_mb <= 0 or args.verification_timeout < 0:
        parser.error("Limits must be non-negative and --max-mb must be positive")
    if args.cookies and not args.cookies.is_file():
        parser.error("Cookie file does not exist")
    state_path = args.browser_state.resolve()
    for path in (args.browser_state, args.cookies):
        if path and path.resolve().is_relative_to(ROOT) and not path.resolve().is_relative_to(PRIVATE_DIR):
            parser.error("Keep repository browser state and cookie exports inside .scraping/, outside data/ and git")
    if bool(args.import_file) != bool(args.url) or (args.import_file and (len(names) != 1 or SOURCES[names[0]].deferred)):
        parser.error("Import requires one enabled source, --import-file and --url")
    incomplete = False
    try:
        with ExitStack() as stack:
            collector = Collector(stack, args.index.resolve(), args.output.resolve(), args.delay, args.max_mb * 1024 * 1024, args.headed,
                                  state_path, args.cookies, args.verification_timeout, args.browser_channel, args.refresh)
            if args.import_file:
                if args.import_file.resolve().is_relative_to(PRIVATE_DIR):
                    parser.error("Private browser state cannot be imported into the dataset")
                url = normalize(args.url)
                if not url:
                    parser.error("Import URL must be HTTP(S)")
                content_type = args.content_type or mimetypes.guess_type(args.import_file.name)[0] or "application/octet-stream"
                collector.save(names[0], url, args.import_file.read_bytes(), url, content_type, "browser-import")
                print(f"[{names[0]}] imported {url}; rerun the source to discover its links")
                return
            for name in names:
                try:
                    incomplete |= collect(collector, name, SOURCES[name], args.max_pages)
                except Exception as error:
                    collector.record(name, None, "incomplete", error=str(error)[:500])
                    print(f"[{name}] stopped: {error}", flush=True)
                    incomplete = True
    except KeyboardInterrupt:
        print("Stopped safely. Rerun the same command to resume.", flush=True)
        raise SystemExit(130)
    raise SystemExit(1 if incomplete else 0)


if __name__ == "__main__":
    main()
