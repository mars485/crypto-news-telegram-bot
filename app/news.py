"""Collect world and crypto news published during the last 24 hours."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import logging

import feedparser
import httpx

logger = logging.getLogger(__name__)

RSS_TIMEOUT_SECONDS = 15.0

@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str
    published_at: datetime | None

RSS_FEEDS = {
    "BBC": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
}

def _parse_date(entry) -> datetime | None:
    value = entry.get("published") or entry.get("updated")
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None

def _load_feed(source: str, url: str):
    response = httpx.get(url, timeout=RSS_TIMEOUT_SECONDS, follow_redirects=True)
    response.raise_for_status()
    return source, feedparser.parse(response.content)

def fetch_news(limit: int = 20, hours: int = 24) -> list[NewsItem]:
    """Fetch RSS concurrently, deduplicate and filter recent articles."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items: list[NewsItem] = []
    seen_urls: set[str] = set()
    successful_feeds = 0

    with ThreadPoolExecutor(max_workers=len(RSS_FEEDS)) as pool:
        futures = {
            pool.submit(_load_feed, source, url): source
            for source, url in RSS_FEEDS.items()
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                _, feed = future.result()
            except (httpx.HTTPError, ValueError) as exc:
                logger.warning("RSS source %s unavailable: %s", source, type(exc).__name__)
                continue
            successful_feeds += 1
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                published_at = _parse_date(entry)
                if not title or not url or url in seen_urls:
                    continue
                if published_at is None or published_at < cutoff:
                    continue
                seen_urls.add(url)
                items.append(NewsItem(title, url, source, published_at))

    if successful_feeds == 0:
        raise RuntimeError("All RSS sources are unavailable")

    items.sort(key=lambda item: item.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    logger.info("RSS loaded: %s sources, %s recent articles", successful_feeds, len(items))
    return items[:limit]
