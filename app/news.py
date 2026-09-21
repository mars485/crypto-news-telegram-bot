"""Collect world and crypto news published during the last 24 hours."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser


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


def fetch_news(limit: int = 20, hours: int = 24) -> list[NewsItem]:
    """Fetch, deduplicate and filter news published within the last N hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items: list[NewsItem] = []
    seen_urls: set[str] = set()

    for source, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
        except Exception:
            continue

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()
            published_at = _parse_date(entry)

            if not title or not url or url in seen_urls:
                continue

            if published_at is None or published_at < cutoff:
                continue

            seen_urls.add(url)
            items.append(
                NewsItem(
                    title=title,
                    url=url,
                    source=source,
                    published_at=published_at,
                )
            )

    items.sort(
        key=lambda item: item.published_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return items[:limit]
