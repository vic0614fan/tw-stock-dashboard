import re
from datetime import datetime, timezone

import feedparser

# CLAUDE.md 指定先用 Yahoo 股市，避免直接爬付費/有爭議來源；
# 鉅亨網目前找不到公開穩定的 RSS，之後有機會再補
RSS_FEEDS = [
    {"source": "yahoo_stock", "category": "tw-market", "url": "https://tw.stock.yahoo.com/rss?category=tw-market"},
    {"source": "yahoo_stock", "category": "news", "url": "https://tw.stock.yahoo.com/rss?category=news"},
]


def normalize_title(title: str) -> str:
    """去除空白與標點，供標題相似度比對用。"""
    return re.sub(r"[\s\W_]+", "", title, flags=re.UNICODE)


def fetch_all_feeds() -> list[dict]:
    items = []
    for feed in RSS_FEEDS:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries:
            published_at = None
            if getattr(entry, "published_parsed", None):
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            items.append(
                {
                    "source": feed["source"],
                    "category": feed["category"],
                    "title": entry.title,
                    "title_normalized": normalize_title(entry.title),
                    "url": entry.link,
                    "published_at": published_at,
                    "description": getattr(entry, "summary", ""),
                }
            )
    return items
