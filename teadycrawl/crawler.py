from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
from urllib.parse import urlparse, urldefrag
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.robotparser import RobotFileParser
from email.utils import parsedate_to_datetime
import json, time
from datetime import datetime, timezone
from .extract import extract_page


@dataclass
class CrawlConfig:
    user_agent: str = "SteadyCrawl/0.1 (+https://github.com/techninxa/steadycrawl)"
    request_timeout: float = 12.0
    max_pages: int = 25
    max_retries: int = 2
    per_host_delay: float = 1.0
    respect_robots_txt: bool = True
    same_origin_only: bool = True
    max_response_bytes: int = 2_000_000


@dataclass
class CrawlResult:
    url: str
    status: int | None
    title: str = ""
    text: str = ""
    links: list[str] = field(default_factory=list)
    error: str | None = None


class PoliteCrawler:
    def __init__(self, config: CrawlConfig | None = None):
        self.config = config or CrawlConfig()
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser | None] = {}

    @staticmethod
    def _origin(url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    def _allowed(self, url: str) -> bool:
        if not self.config.respect_robots_txt:
            return True
        origin = self._origin(url)
        if origin not in self._robots:
            robots_url = origin + "/robots.txt"
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                req = Request(robots_url, headers={"User-Agent": self.config.user_agent})
                with urlopen(req, timeout=self.config.request_timeout) as response:
                    content = response.read(256_000).decode("utf-8", "replace")
                parser.parse(content.splitlines())
                self._robots[origin] = parser
            except HTTPError as exc:
                # A missing robots.txt is treated as no published restriction.
                if exc.code == 404:
                    self._robots[origin] = None
                else:
                    # Fail closed on access errors rather than guessing permission.
                    self._robots[origin] = False
            except Exception:
                self._robots[origin] = False
        parser = self._robots[origin]
        if parser is False:
            return False
        return True if parser is None else parser.can_fetch(self.config.user_agent, url)

    def _wait(self, url: str):
        origin = self._origin(url)
        delay = max(0.0, self.config.per_host_delay)
        remaining = delay - (time.monotonic() - self._last_request.get(origin, 0.0))
        if remaining > 0:
            time.sleep(remaining)
        self._last_request[origin] = time.monotonic()

    @staticmethod
    def _retry_after(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return max(0.0, min(60.0, float(value)))
        except ValueError:
            try:
                dt = parsedate_to_datetime(value)
                return max(0.0, min(60.0, (dt - datetime.now(timezone.utc)).total_seconds()))
            except Exception:
                return None

    def fetch(self, url: str) -> CrawlResult:
        if urlparse(url).scheme not in {"http", "https"}:
            return CrawlResult(url, None, error="Only HTTP and HTTPS URLs are supported.")
        if not self._allowed(url):
            return CrawlResult(url, None, error="Blocked by robots.txt or robots policy could not be verified.")
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            self._wait(url)
            req = Request(url, headers={"User-Agent": self.config.user_agent, "Accept": "text/html,application/xhtml+xml"})
            try:
                with urlopen(req, timeout=self.config.request_timeout) as response:
                    status = response.status
                    content_type = response.headers.get("Content-Type", "")
                    if "html" not in content_type.lower():
                        return CrawlResult(url, status, error=f"Skipped non-HTML content: {content_type}")
                    body = response.read(self.config.max_response_bytes + 1)
                    if len(body) > self.config.max_response_bytes:
                        return CrawlResult(url, status, error="Response exceeded max_response_bytes.")
                    html = body.decode(response.headers.get_content_charset() or "utf-8", "replace")
                    page = extract_page(html, url)
                    return CrawlResult(url, status, page.title, page.text, page.links)
            except HTTPError as exc:
                last_error = f"HTTP {exc.code}"
                if exc.code not in {429, 500, 502, 503, 504} or attempt >= self.config.max_retries:
                    return CrawlResult(url, exc.code, error=last_error)
                delay = self._retry_after(exc.headers.get("Retry-After")) or min(2 ** attempt, 10)
            except (URLError, TimeoutError, OSError) as exc:
                last_error = str(exc)
                if attempt >= self.config.max_retries:
                    break
                delay = min(2 ** attempt, 10)
            time.sleep(delay)
        return CrawlResult(url, None, error=last_error or "Request failed.")

    def crawl(self, seeds: list[str]) -> list[CrawlResult]:
        if not seeds:
            return []
        seed_origins = {self._origin(u) for u in seeds}
        queue = deque(seeds)
        seen = set()
        results = []
        while queue and len(results) < self.config.max_pages:
            url, _ = urldefrag(queue.popleft())
            if url in seen:
                continue
            seen.add(url)
            if self.config.same_origin_only and self._origin(url) not in seed_origins:
                continue
            result = self.fetch(url)
            results.append(result)
            if result.status and result.status < 400:
                for link in result.links:
                    if link not in seen and (not self.config.same_origin_only or self._origin(link) in seed_origins):
                        queue.append(link)
        return results


def result_to_dict(result: CrawlResult) -> dict:
    return {
        "url": result.url, "status": result.status, "title": result.title,
        "text": result.text, "links": result.links, "error": result.error,
    }
