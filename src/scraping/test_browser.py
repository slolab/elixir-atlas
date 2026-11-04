from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest

from browser import Browser, VerificationRequired, challenge, read_state


class BrowserTests(unittest.TestCase):
    def test_common_challenges_and_normal_embedded_widget(self):
        self.assertTrue(challenge('<title>Loading</title>', {'cf-mitigated': 'challenge'}))
        for html in ('<title>Just a moment...</title>', '<div id="px-captcha"></div>',
                     '<p>Please verify you are human</p>', '<p>Unusual traffic from your computer</p>'):
            self.assertTrue(challenge(html))
        self.assertIsNone(challenge('<title>Contact us</title><script src="https://www.google.com/recaptcha/api.js"></script><p>Our team</p>'))
        self.assertIsNone(challenge('<title>Access denied | ELIXIR</title><div id="block-elixir2-accessdeniedanonymous">The ELIXIR intranet is for members of ELIXIR</div>'))

    def test_browser_cookie_export(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cookies.json"
            path.write_text(json.dumps([{"name": "clearance", "value": "fixture", "domain": "example.org",
                                         "expirationDate": 2000000000, "sameSite": "no_restriction", "hostOnly": True, "secure": 1,
                                         "partitionKey": "https://example.org"}]))
            cookie = read_state(path)["cookies"][0]
            self.assertEqual(cookie["sameSite"], "None")
            self.assertEqual(cookie["expires"], 2000000000)
            self.assertEqual(cookie["path"], "/")
            self.assertIs(cookie["secure"], True)
            self.assertEqual(cookie["partitionKey"], "https://example.org")
            self.assertNotIn("hostOnly", cookie)

    def test_cookie_initialization_manual_resume_and_document_session(self):
        class Handler(BaseHTTPRequestHandler):
            received = {}

            def do_GET(self):
                self.received[self.path] = dict(self.headers)
                if self.headers.get('Host', '').startswith('www.localhost:'):
                    self.send_response(302)
                    self.send_header('Location', f'http://localhost:{self.server.server_port}{self.path}')
                    self.end_headers()
                    return
                cleared = "clearance=fixture" in self.headers.get("Cookie", "")
                body = b'<html><title>Just a moment...</title><button onclick="document.cookie=\'clearance=fixture; path=/\'; location.reload()">Complete fixture</button></html>'
                if cleared:
                    body = b'%PDF-1.4 fixture' if self.path.endswith('.pdf') else b'<html><title>Collected page</title></html>'
                self.send_response(200 if cleared else 403)
                self.send_header('Content-Type', 'application/pdf' if cleared and self.path.endswith('.pdf') else 'text/html')
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            Thread(target=server.serve_forever, daemon=True).start()
            stack.callback(server.server_close)
            stack.callback(server.shutdown)
            url = f'http://127.0.0.1:{server.server_port}'
            state = Path(directory) / 'session.json'
            imported = Path(directory) / 'import.json'
            imported.write_text(json.dumps([{'name': 'clearance', 'value': 'fixture', 'domain': '127.0.0.1', 'path': '/'}]))
            with ExitStack() as browser_stack:
                browser = Browser(browser_stack, state, imported, channel="chromium")
                body, _, _, _ = browser.fetch(url + '/page', False, 10000, self.fail)
                self.assertIn(b'Collected page', body)
                signals = browser.page.evaluate('({ua: navigator.userAgent, webdriver: navigator.webdriver, language: navigator.language})')
                self.assertFalse(signals['webdriver'])
                self.assertNotIn('HeadlessChrome', signals['ua'])
                self.assertNotIn('Playwright', signals['ua'])
                self.assertEqual(Handler.received['/page']['User-Agent'], signals['ua'])
                self.assertTrue(Handler.received['/page']['Accept-Language'].startswith(signals['language']))
                browser.context.clear_cookies()
                browser.headed = False
                with self.assertRaises(VerificationRequired):
                    browser.fetch(url + '/page', False, 10000, lambda reason: None)
                browser.headed = True
                blocked = []

                def complete_fixture(reason):
                    blocked.append(reason)

                    browser.page.get_by_text('Complete fixture').click()
                    browser.page.wait_for_function('document.title === "Collected page"')

                body, _, _, _ = browser.fetch(url + '/page', False, 10000, complete_fixture)
                self.assertEqual(len(blocked), 1)
                self.assertIn(b'Collected page', body)
                self.assertTrue(state.exists())
                pdf, _, content_type, _ = browser.fetch(url + '/document.pdf', True, 10000, self.fail)
                self.assertEqual(content_type, 'application/pdf')
                self.assertTrue(pdf.startswith(b'%PDF'))
                self.assertEqual(Handler.received['/document.pdf']['User-Agent'], signals['ua'])
                self.assertIn('sec-ch-ua', {k.lower() for k in Handler.received['/document.pdf']})
                browser.page.evaluate('localStorage.setItem("persistent-fixture", "kept")')
                browser.context.add_cookies([{'name': 'clearance', 'value': 'fixture', 'domain': 'localhost', 'path': '/'}])
                pdf, final_url, _, _ = browser.fetch(f'http://www.localhost:{server.server_port}/document.pdf', True, 10000, self.fail)
                self.assertTrue(pdf.startswith(b'%PDF'))
                self.assertEqual(final_url, f'http://localhost:{server.server_port}/document.pdf')
            self.assertEqual(state.stat().st_mode & 0o777, 0o600)
            with ExitStack() as browser_stack:
                browser = Browser(browser_stack, state, channel="chromium")
                body, _, _, _ = browser.fetch(url + '/page', False, 10000, self.fail)
                self.assertIn(b'Collected page', body)
                self.assertEqual(browser.page.evaluate('localStorage.getItem("persistent-fixture")'), 'kept')


if __name__ == '__main__':
    unittest.main()
