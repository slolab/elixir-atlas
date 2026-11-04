from contextlib import ExitStack, redirect_stderr
from io import StringIO
import json
import re
from pathlib import Path
import tempfile
import unittest

import httpx

from run import Collector, collect, main
from browser import VerificationRequired
from discovery import Discovery, website, f1000, tess, zenodo, normalize, page_allowed, pagination_url
from dataclasses import replace
from unittest.mock import patch

def html_links(body, current, source):
    return source.discover(body.encode() if isinstance(body, str) else body, current, "text/html", source).links
from sources import SOURCES


class ScrapingTests(unittest.TestCase):
    def test_private_state_and_cookie_exports_cannot_live_in_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            cookie_file = root / "data" / "cookies.json"
            cookie_file.parent.mkdir()
            cookie_file.write_text("[]")
            cases = (
                ["--cookies", str(cookie_file)],
                ["--browser-state", str(root / "data" / "session.json")],
                ["--browser-state", str(root / "session.json")],
            )
            for arguments in cases:
                with self.subTest(arguments=arguments), patch("run.ROOT", root), patch("run.PRIVATE_DIR", root / ".scraping"), patch("sys.argv", ["run.py", "elixir", *arguments]), patch("run.Collector") as collector, redirect_stderr(StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        main()
                    self.assertEqual(error.exception.code, 2)
                    collector.assert_not_called()

    def test_biotools_next_keeps_page_size_and_format(self):
        url = pagination_url("https://bio.tools/api/t/?format=json&per_page=100", "?page=2", "biotools")
        self.assertEqual(url, "https://bio.tools/api/t/?format=json&page=2&per_page=100")

    def test_tess_next_keeps_history_and_json_format(self):
        url = pagination_url("https://tess.elixir-europe.org/events.json_api?include_expired=true&page_size=100",
                             "/events?page_number=2", "tess")
        self.assertEqual(url, "https://tess.elixir-europe.org/events.json_api?include_expired=true&page_number=2&page_size=100")

    def test_website_boundaries(self):
        source = SOURCES["node-spain"]
        self.assertTrue(page_allowed("https://inb-elixir.es/news", source))
        for url in ("https://elsewhere.es/news", "https://inb-elixir.es/user/login",
                    "https://inb-elixir.es/events?month=2099-12", "https://inb-elixir.es/logo.png"):
            self.assertFalse(page_allowed(url, source), url)
        self.assertEqual(normalize("https://inb-elixir.es/news?utm_source=email#top"), "https://inb-elixir.es/news")
        self.assertFalse(page_allowed("https://elixir-europe.org/users/tereza2", SOURCES["elixir"]))

    def test_news_listings_do_not_expand_into_articles_or_archives(self):
        for name, listing in [('elixir', 'https://elixir-europe.org/news'),
                              ('node-uk', 'https://elixiruknode.org/news-and-stories'),
                              ('node-germany', 'https://www.denbi.de/news1'),
                              ('node-spain', 'https://inb-elixir.es/news')]:
            source = SOURCES[name]
            self.assertTrue(page_allowed(listing + '/', source))
            self.assertFalse(page_allowed(listing + '?page=2', source))
            self.assertFalse(page_allowed(listing + '/old-article', source))
            self.assertEqual(list(html_links('<a href="/report.pdf">Report</a>', listing, source)), [])
        self.assertFalse(page_allowed('https://inb-elixir.es/jobs/example', SOURCES['node-spain']))
        self.assertFalse(page_allowed('https://www.denbi.de/training-archive-sorted-according-by-date/old-course', SOURCES['node-germany']))
        self.assertTrue(page_allowed('https://elixir-europe.org/events/demystifying-elixir-everything-you-ever-wanted-know-and-more', SOURCES['elixir']))

    def test_links_keep_documents_but_do_not_crawl_external_sites(self):
        html = '<a href="https://[broken]">Broken</a><a href="/people">People</a><a href="https://example.org/">External</a><a href="https://example.org/report.pdf">PDF</a><a href="https://youtu.be/example">Video</a>'
        links = set(html_links(html, "https://elixiruknode.org/", SOURCES["node-uk"]))
        self.assertEqual(links, {("https://elixiruknode.org/people", "download"),
                                ("https://example.org/report.pdf", "download"), ("https://youtu.be/example", "video")})

    def test_failed_download_is_not_saved_and_success_is_reused(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            collector = Collector(stack, root / "index.jsonl", root / "raw", 0, 10000, False)
            requests = []

            def respond(request):
                requests.append(request.url.path)
                if request.url.path == "/robots.txt":
                    return httpx.Response(200, text="User-agent: *\n")
                if request.url.path == "/missing":
                    return httpx.Response(404)
                return httpx.Response(200, text="<html><title>Real page</title></html>", headers={"content-type": "text/html"})

            collector.client = stack.enter_context(httpx.Client(transport=httpx.MockTransport(respond)))
            self.assertIsNone(collector.fetch("test", "https://example.org/missing"))
            self.assertIsNone(collector.fetch("test", "https://example.org/not-really.pdf"))
            first = collector.fetch("test", "https://example.org/page")
            second = collector.fetch("test", "https://example.org/page")
            self.assertEqual(first[0], second[0])
            self.assertTrue(second[2])
            self.assertEqual(requests.count("/page"), 1)
            rows = [json.loads(line) for line in (root / "index.jsonl").read_text().splitlines()]
            self.assertEqual([row["status"] for row in rows], ["failed", "failed", "saved"])
            self.assertEqual(len(list((root / "raw").rglob("*.html"))), 1)

    def test_registry_covers_every_documented_source(self):
        document = Path(__file__).resolve().parents[2] / "docs/data-sources.md"
        sections = {int(number) for number in re.findall(r"^(\d+)\. \*\*", document.read_text(), re.M)}
        self.assertEqual({section for source in SOURCES.values() for section in source.sections}, sections)
        for source in SOURCES.values():
            self.assertTrue(source.urls or source.deferred)
            self.assertTrue(callable(source.discover))
        self.assertTrue(any("elixir-programme-24-28-full.pdf" in url for url in SOURCES["elixir"].urls))
        self.assertTrue(any("drive.google.com/file" in url for url in SOURCES["elixir"].urls))

    def test_f1000_script_links_and_cdn_downloads(self):
        body = b'''<span class="js-pagination-results-total">2</span><script>
        var channelHTML = '<a href="/posters/15-1">one</a><a href="/posters/15-2">two</a>';
        </script><a class="js-pagination-next" href="?selectedDomain=posters&page=2">Next</a>'''
        found = f1000(body, "https://f1000research.com/gateways/elixir?selectedDomain=posters", "text/html", SOURCES["f1000"])
        self.assertEqual(found.ids, ["15-1", "15-2"])
        self.assertEqual(found.total, 2)
        self.assertEqual(len(found.links), 3)
        pdf = b'<a class="js-download" data-url="https://f1000research-files.f1000.com/posters/docs/example.pdf">Download</a>'
        found = f1000(pdf, "https://f1000research.com/posters/15-1", "text/html", SOURCES["f1000"])
        self.assertEqual(found.links, [("https://f1000research-files.f1000.com/posters/docs/example.pdf", "download")])
        with self.assertRaises(ValueError):
            f1000(b'<span class="js-pagination-results-total">2</span>', "https://f1000research.com/gateways/elixir", "text/html", SOURCES["f1000"])

    def test_zenodo_preserves_html_and_spreadsheet_attachments(self):
        body = json.dumps({"files": [{"key": name, "links": {"self": f"https://zenodo.org/api/records/1/files/{name}/content"}} for name in ("deck.html", "data.ods", "video.mp4")]}).encode()
        found = zenodo(body, "https://zenodo.org/api/records/1", "application/json", SOURCES["zenodo"])
        self.assertEqual([action for _, action in found.links], ["download", "download", "video"])
        self.assertEqual(zenodo(b'<a href="https://example.org/">x</a>', found.links[0][0], "text/html", SOURCES["zenodo"]).links, [])

    def test_interruption_resumes_and_new_discovery_reuses_raw_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = replace(SOURCES["node-uk"], urls=("https://example.org/",))
            requests = []
            interrupt = True

            def respond(request):
                nonlocal interrupt
                requests.append(request.url.path)
                if request.url.path == "/robots.txt":
                    return httpx.Response(200, text="User-agent: *\n")
                if request.url.path == "/child" and interrupt:
                    interrupt = False
                    raise KeyboardInterrupt()
                html = '<title>Page</title><a href="/child">Child</a>' if request.url.path == "/" else '<title>Child</title>'
                return httpx.Response(200, text=html, headers={"content-type": "text/html"})

            def make(stack):
                collector = Collector(stack, root / "index.jsonl", root / "raw", 0, 10000, False)
                collector.client = stack.enter_context(httpx.Client(transport=httpx.MockTransport(respond)))
                return collector

            with ExitStack() as stack:
                first = make(stack)
                with self.assertRaises(KeyboardInterrupt):
                    collect(first, "test", source)
                self.assertEqual(first.latest["test", "https://example.org/child"]["status"], "pending")

            with (root / "index.jsonl").open("ab") as f:
                f.write(b'{"source":')
            with ExitStack() as stack:
                second = make(stack)
                self.assertFalse(collect(second, "test", source))
                self.assertEqual(requests.count("/"), 1)
                self.assertEqual(requests.count("/child"), 2)
                self.assertEqual(second.latest["test", "https://example.org/child"]["discovered_from"], "https://example.org/")
            def fixed_discovery(body, url, content_type, src):
                found = website(body, url, content_type, src)
                if url == "https://example.org/":
                    found.links.append(("https://example.org/missed", "download"))
                return found
            with ExitStack() as stack:
                third = make(stack)
                self.assertFalse(collect(third, "test", replace(source, discover=fixed_discovery)))
                self.assertEqual(requests.count("/"), 1)
                self.assertEqual(requests.count("/missed"), 1)
                third.refresh = True
                third.fetch("test", "https://example.org/")
                self.assertEqual(requests.count("/"), 2)
                cached = third.cache["test", "https://example.org/"]
                Path(cached["path"]).write_bytes(b"partial")
                third.refresh = False
                third.fetch("test", "https://example.org/")
                self.assertEqual(requests.count("/"), 3)

    def test_discovery_errors_do_not_erase_download_success(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            collector = Collector(stack, root / "index.jsonl", root / "raw", 0, 10000, False)
            url = "https://example.org/"
            collector.save("test", url, b'<title>Bad listing</title>', url, "text/html", "browser-import")
            def broken(*args):
                raise ValueError("No records found")
            source = replace(SOURCES["node-uk"], urls=(url,), discover=broken)
            self.assertTrue(collect(collector, "test", source))
            self.assertEqual(collector.latest["test", url]["status"], "saved")
            self.assertEqual(collector.latest["test", url]["discovery_status"], "failed")
            self.assertFalse(collect(collector, "test", replace(source, discover=website)))
            self.assertEqual(collector.latest["test", url]["discovery_status"], "complete")

    def test_changing_catalogue_totals_and_duplicate_ids_are_incomplete(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            collector = Collector(stack, root / "index.jsonl", root / "raw", 0, 10000, False)
            urls = ("https://example.org/events.json_api?page_number=1", "https://example.org/events.json_api?page_number=2")
            for url, ids, total in ((urls[0], ["a", "b"], 2), (urls[1], ["b", "c"], 3)):
                body = json.dumps({"data": [{"id": id_} for id_ in ids], "links": {"next": urls[1] if url == urls[0] else None}, "meta": {"results-count": total}}).encode()
                collector.save("test", url, body, url, "application/json", "response")
            self.assertTrue(collect(collector, "test", replace(SOURCES["tess-events"], urls=urls[:1])))
            check = collector.latest["test", None]["catalogues"]["tess"]
            self.assertEqual(check["reported_totals"], [2, 3])
            self.assertEqual(check["duplicates"], 1)
            self.assertFalse(check["matched"])

    def test_source_formats_and_drive_viewer_stay_scoped(self):
        source = replace(SOURCES["node-uk"], formats=frozenset({".ods", ".custom"}))
        html = b'<a href="https://example.org/data.custom">Data</a><a href="https://example.org/report.pdf">PDF</a>'
        self.assertEqual(website(html, "https://elixiruknode.org/", "text/html", source).links,
                         [("https://example.org/data.custom", "download")])
        url = "https://drive.google.com/file/d/example/view"
        self.assertEqual(website(b'<a href="/unrelated">Other</a>', url, "text/html", source).links,
                         [("https://drive.google.com/uc?export=download&id=example", "download")])

    def test_one_blocked_host_does_not_stop_other_downloads(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            collector = Collector(stack, root / "index.jsonl", root / "raw", 0, 10000, False)
            urls = ("https://blocked.example/one", "https://blocked.example/two", "https://working.example/page")
            requests = []
            def request(url, *args):
                requests.append(url)
                if "blocked.example" in url:
                    raise VerificationRequired("Manual check timed out")
                return b"<title>Page</title>", url, "text/html", "response"
            collector.request = request
            collector.permitted = lambda url: True
            self.assertTrue(collect(collector, "test", replace(SOURCES["node-uk"], urls=urls)))
            self.assertEqual(requests, [urls[0], urls[2]])
            self.assertEqual(collector.latest["test", urls[2]]["status"], "saved")
            self.assertEqual(collector.latest["test", urls[1]]["status"], "blocked")

    def test_atomic_save_does_not_publish_partial_file(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            collector = Collector(stack, root / "index.jsonl", root / "raw", 0, 10000, False)
            with patch.object(Path, "replace", side_effect=OSError("interrupted write")):
                with self.assertRaises(OSError):
                    collector.save("test", "https://example.org/page", b"<title>Page</title>", "https://example.org/page", "text/html", "response")
            self.assertEqual(list((root / "raw").rglob("*.html")), [])
            self.assertTrue(all(p.name.startswith(".") for p in (root / "raw").rglob("*.part")))
            self.assertNotIn(("test", "https://example.org/page"), collector.cache)


if __name__ == "__main__":
    unittest.main()
