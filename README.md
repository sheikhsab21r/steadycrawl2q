# SteadyCrawl

**A small, polite, robots-aware Python crawler for dependable website data collection.**

SteadyCrawl focuses on the reliability work that simple scraping scripts often omit: robots.txt checks, per-host pacing, bounded retries, `Retry-After` handling, response-size limits, same-origin crawling, and structured page extraction.

It is designed for public pages you are permitted to access. It does **not** bypass CAPTCHAs, authentication, paywalls, access controls, or anti-bot protections.

## Features

- Python 3.10+, standard library only.
- Checks `robots.txt` before fetching pages by default.
- Fails closed when robots policy cannot be verified due to access errors.
- Per-host request pacing.
- Retries transient network errors and HTTP 429/5xx responses.
- Honors numeric or HTTP-date `Retry-After` values (bounded to 60 seconds).
- Same-origin crawling by default.
- Extracts page title, readable text, and absolute links.
- Limits response size and request timeout.
- JSON Lines output from the command line.

## Install

```bash
python -m pip install .
```

For development:

```bash
python -m unittest discover -s tests -v
```

## Quick start

```bash
steadycrawl https://example.com --max-pages 5 --delay 1.5
```

Each output line is a JSON object containing `url`, `status`, `title`, `text`, `links`, and `error`.

## Python API

```python
from steadycrawl import CrawlConfig, PoliteCrawler

crawler = PoliteCrawler(CrawlConfig(
    max_pages=20,
    per_host_delay=1.0,
    respect_robots_txt=True,
    same_origin_only=True,
))

for page in crawler.crawl(["https://example.com"]):
    if page.error:
        print("Skipped/failed:", page.url, page.error)
    else:
        print(page.title, page.url)
```

Fetch a single URL:

```python
page = crawler.fetch("https://example.com/about")
```

## Configuration

| Option | Default | Meaning |
|---|---:|---|
| `user_agent` | `SteadyCrawl/0.1 (+https://github.com/techninxa/steadycrawl)` | Identify your crawler. Replace with a real project URL/contact before public release. |
| `request_timeout` | `12.0` | Timeout in seconds. |
| `max_pages` | `25` | Maximum pages returned by `crawl`. |
| `max_retries` | `2` | Retries after the first attempt. |
| `per_host_delay` | `1.0` | Minimum interval between requests to the same host. |
| `respect_robots_txt` | `True` | Check published crawler rules. |
| `same_origin_only` | `True` | Do not follow links to other origins. |
| `max_response_bytes` | `2_000_000` | Maximum HTML response body size. |

## Responsible-use guidance

1. Crawl only public pages you are permitted to access.
2. Keep a descriptive User-Agent and provide a contact route in your production configuration.
3. Respect robots.txt, site terms, rate limits, and applicable law.
4. Do not attempt to evade CAPTCHAs, login requirements, IP blocks, or other access controls.
5. Stop if a site owner asks you to stop.
6. Use conservative delays and narrow page limits.
7. Store only data you have a lawful basis to collect.

`robots.txt` is a crawler coordination standard, not a grant of legal permission. A site's terms and applicable law still matter.

## Known limitations

- HTML extraction is intentionally lightweight; it does not execute JavaScript.
- No browser automation or dynamic-page rendering.
- No proxy rotation or anti-bot evasion.
- No persistent crawl database, distributed scheduling, or concurrency.
- Robots policy is cached for the lifetime of a crawler instance.
- This is an initial 0.1 release; validate against your own permitted sites before production use.

## Contributing

Issues and pull requests are welcome. Please include a minimal reproduction, expected behavior, and tests for bug fixes. Keep changes respectful of site operators and the responsible-use policy.

## Roadmap

- Persistent cache and conditional requests (`ETag`, `Last-Modified`).
- Sitemap discovery.
- Configurable content extractors.
- Structured crawl statistics and export formats.
- Optional proxy support for legitimate network routing, without access-control evasion.

## License

MIT. See [LICENSE](LICENSE).
