"""Collect recent world news from RSS feeds."""

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str
    published_at: datetime | None


RSS_FEEDS = {
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "BBC": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
}


def _parse_date(entry) -> datetime | None:
    value = entry.get("published") or entry.get("updated")
    if not value:
        return None

    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def fetch_news(limit: int = 20) -> list[NewsItem]:
    """Fetch and normalize recent items from configured RSS feeds."""
    items: list[NewsItem] = []

    for source, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
        except Exception:
            continue

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()

            if not title or not url:
                continue

            items.append(
                NewsItem(
                    title=title,
                    url=url,
                    source=source,
                    published_at=_parse_date(entry),
                )
            )

    items.sort(
        key=lambda item: item.published_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return items[:limit]
