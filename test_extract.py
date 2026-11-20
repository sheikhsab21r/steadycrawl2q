import unittest
from steadycrawl.extract import extract_page

class ExtractTests(unittest.TestCase):
    def test_extracts_title_text_and_absolute_links(self):
        page = extract_page('<html><title>Example</title><body>Hello <script>bad()</script><a href="/next">Next</a></body></html>', 'https://example.com/start')
        self.assertEqual(page.title, "Example")
        self.assertIn("Hello", page.text)
        self.assertNotIn("bad()", page.text)
        self.assertIn("https://example.com/next", page.links)

if __name__ == "__main__":
    unittest.main()
