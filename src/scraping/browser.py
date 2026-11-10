import base64
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from playwright.sync_api import Error, sync_playwright


class VerificationRequired(RuntimeError):
    pass


def challenge(body, headers=None):
    if headers and headers.get("cf-mitigated") == "challenge":
        return "Cloudflare challenge"
    soup = BeautifulSoup(body, "html.parser")


    if soup.select_one("#block-elixir2-accessdeniedanonymous"):
        return None
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = soup.get_text(" ", strip=True)[:3000]
    if re.search(r"just a moment|attention required|security (check|verification)|robot check|are you (a robot|human)|access denied|captcha", title, re.I):
        return title
    if soup.select_one('#challenge-form, #cf-challenge-running, #px-captcha, form[action*="/sorry/"]'):
        return "Browser verification"
    if re.search(r"verify (that )?you (are|are a) human|checking your browser|unusual traffic from your computer|complete the security check|enable javascript and cookies to continue", text, re.I):
        return "CAPTCHA or browser verification"
    return None


def read_state(path):
    data = json.loads(Path(path).read_text())
    state = {"cookies": data, "origins": []} if isinstance(data, list) else data
    cookies = []
    for item in state["cookies"]:
        cookie = {key: item[key] for key in ("name", "value", "domain", "path", "url", "httpOnly", "secure", "expires", "partitionKey") if key in item}
        for key in ("httpOnly", "secure"):
            if key in cookie:
                cookie[key] = bool(cookie[key])
        if "expirationDate" in item and "expires" not in cookie:
            cookie["expires"] = item["expirationDate"]
        same_site = str(item.get("sameSite", "Lax")).lower()
        cookie["sameSite"] = {"strict": "Strict", "lax": "Lax", "none": "None", "no_restriction": "None", "unspecified": "Lax"}.get(same_site, "Lax")
        if "domain" in cookie:
            cookie.setdefault("path", "/")
        cookies.append(cookie)
    return {"cookies": cookies, "origins": state.get("origins", [])}


def merge_cookies(*groups):
    return list({(c["name"], c.get("domain", c.get("url")), c.get("path", "/"), c.get("partitionKey")): c
                 for group in groups for c in group}.values())


class Browser:
    def __init__(self, stack, state_path, cookies=None, headed=True, timeout=0, channel="chrome"):
        self.state_path, self.headed, self.timeout = Path(state_path), headed, timeout
        state = read_state(self.state_path) if self.state_path.exists() else {"cookies": [], "origins": []}
        imported = {"cookies": [], "origins": []}
        if cookies:
            imported = read_state(cookies)

            state = {"cookies": merge_cookies(state["cookies"], imported["cookies"]), "origins": imported["origins"] or state["origins"]}
        playwright = stack.enter_context(sync_playwright())
        profile = self.state_path.with_name(f"{self.state_path.stem}-{channel}-profile")
        first_use = not profile.exists()
        profile.mkdir(parents=True, exist_ok=True, mode=0o700)


        self.context = playwright.chromium.launch_persistent_context(
            profile, channel=channel, headless=not headed, no_viewport=True,
            chromium_sandbox=True, color_scheme="null",
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled", "--window-size=1440,900"],
        )
        stack.callback(self.close)
        if first_use or imported["origins"]:
            self.context.set_storage_state(state)
        else:

            self.context.add_cookies(merge_cookies(state["cookies"], self.context.cookies(), imported["cookies"]))
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

    def save_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(self.context.storage_state(), f)
        temporary.replace(self.state_path)

    def close(self):
        try:
            self.save_state()
        except Error:
            pass
        self.context.close()

    def navigate(self, url, on_block):
        response = self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
        started = time.monotonic()
        while reason := challenge(self.page.content(), response.headers if response else None):
            if self.timeout and time.monotonic() - started >= self.timeout:
                raise VerificationRequired("Manual verification timed out; rerun to resume")
            on_block(reason)
            if not self.headed:
                raise VerificationRequired("Verification needs a visible browser; rerun without --headless")
            self.page.bring_to_front()
            print(f"Paused for verification: {url}\nComplete the check in the browser. Collection resumes automatically; Ctrl+C stops safely.", flush=True)
            while challenge(self.page.content()):
                if self.timeout and time.monotonic() - started >= self.timeout:
                    raise VerificationRequired("Manual verification timed out; rerun to resume")
                self.page.wait_for_timeout(1000)

            self.save_state()
            response = self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
        if response is None or response.status >= 400:
            raise ValueError(f"HTTP {response.status if response else 'unknown'} from browser")
        return response

    def document(self, url, max_bytes, on_block, retried=False):
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(url))
        if urlsplit(self.page.url)[:2] != urlsplit(url)[:2]:
            self.navigate(origin + "/", on_block)
        requested, current = urlsplit(url), urlsplit(self.page.url)


        if requested.hostname.removeprefix("www.") == current.hostname.removeprefix("www."):
            url = urlunsplit((current.scheme, current.netloc, requested.path, requested.query, requested.fragment))


        result = self.page.evaluate("""async ({url, limit}) => {
            const response = await fetch(url, {credentials: 'include', signal: AbortSignal.timeout(45000)});
            const reader = response.body.getReader();
            const parts = [];
            let size = 0;
            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                size += value.length;
                if (size > limit) { await reader.cancel(); throw new Error('Document exceeds size limit'); }
                for (let i = 0; i < value.length; i += 32768)
                    parts.push(String.fromCharCode(...value.subarray(i, i + 32768)));
            }
            return {body: btoa(parts.join('')), url: response.url, status: response.status,
                    headers: Object.fromEntries(response.headers.entries())};
        }""", {"url": url, "limit": max_bytes})
        body = base64.b64decode(result["body"])
        content_type = result["headers"].get("content-type", "").split(";")[0]
        if "html" in content_type and challenge(body, result["headers"]):
            if retried:
                raise VerificationRequired("Document remains blocked after manual verification")
            try:
                self.navigate(url, on_block)
            except Error as error:
                if "Download is starting" not in str(error):
                    raise

            self.navigate(origin + "/", on_block)
            return self.document(url, max_bytes, on_block, retried=True)
        if result["status"] >= 400:
            raise ValueError(f'HTTP {result["status"]} downloading document')
        return body, result["url"], content_type, "response"

    def fetch(self, url, document, max_bytes, on_block, wait_for=None):
        try:
            if document:
                return self.document(url, max_bytes, on_block)
            self.navigate(url, on_block)
            if wait_for:
                self.page.locator(wait_for).first.wait_for(state="attached", timeout=20000)
            body = self.page.content().encode()
            if len(body) > max_bytes:
                raise ValueError("Page exceeds download size limit")
            return body, self.page.url, "text/html", "rendered-html"
        except Error as error:
            if self.page.is_closed():
                raise VerificationRequired("Browser closed; rerun to resume") from error

            raise ValueError(f"Browser request failed: {error}") from error
