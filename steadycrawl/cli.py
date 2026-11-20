import argparse, json, sys
from .crawler import CrawlConfig, PoliteCrawler, result_to_dict


def main():
    parser = argparse.ArgumentParser(description="A polite, robots-aware website crawler.")
    parser.add_argument("urls", nargs="+", help="One or more starting URLs")
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--delay", type=float, default=1.0, help="Minimum seconds between requests to the same host")
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--user-agent", default="SteadyCrawl/0.1 (+https://github.com/techninxa/steadycrawl)")
    parser.add_argument("--allow-external", action="store_true", help="Allow links outside the seed origins")
    parser.add_argument("--ignore-robots", action="store_true", help="Not recommended; use only where you have permission")
    args = parser.parse_args()
    if args.max_pages < 1 or args.delay < 0 or args.timeout <= 0:
        parser.error("--max-pages must be positive, --delay non-negative, and --timeout positive")
    config = CrawlConfig(
        user_agent=args.user_agent, max_pages=args.max_pages,
        per_host_delay=args.delay, request_timeout=args.timeout,
        same_origin_only=not args.allow_external,
        respect_robots_txt=not args.ignore_robots,
    )
    results = PoliteCrawler(config).crawl(args.urls)
    for result in results:
        print(json.dumps(result_to_dict(result), ensure_ascii=False))
    if any(r.error for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
