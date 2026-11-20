from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urldefrag


@dataclass
class PageData:
    title: str
    text: str
    links: list[str]


class _Extractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg"}
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts = []
        self.text_parts = []
        self.links = []
        self.in_title = False
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag in self.SKIP:
            self.skip_depth += 1
        if tag == "a" and attrs.get("href"):
            link, _ = urldefrag(urljoin(self.base_url, attrs["href"]))
            if link.startswith(("http://", "https://")):
                self.links.append(link)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        value = " ".join(data.split())
        if not value:
            return
        if self.in_title:
            self.title_parts.append(value)
        if not self.skip_depth:
            self.text_parts.append(value)


def extract_page(html: str, url: str) -> PageData:
    parser = _Extractor(url)
    parser.feed(html)
    return PageData(
        title=" ".join(parser.title_parts).strip(),
        text=" ".join(parser.text_parts).strip(),
        links=list(dict.fromkeys(parser.links)),
    )
