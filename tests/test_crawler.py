import threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from steadycrawl.crawler import CrawlConfig, PoliteCrawler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/robots.txt":
            body = b"User-agent: *\nDisallow: /private\n"
            self.send_response(200); self.send_header("Content-Type", "text/plain"); self.end_headers(); self.wfile.write(body); return
        body = b"<html><title>Local</title><p>Works</p><a href='/next'>Next</a></html>"
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *args): pass

class CrawlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.thread.join(); cls.server.server_close()
    def test_fetches_html(self):
        crawler = PoliteCrawler(CrawlConfig(per_host_delay=0))
        result = crawler.fetch(self.base + "/")
        self.assertEqual(result.status, 200)
        self.assertEqual(result.title, "Local")
        self.assertIn("Works", result.text)
    def test_respects_robots(self):
        crawler = PoliteCrawler(CrawlConfig(per_host_delay=0))
        result = crawler.fetch(self.base + "/private")
        self.assertIsNone(result.status)
        self.assertIn("robots.txt", result.error)

if __name__ == "__main__":
    unittest.main()
