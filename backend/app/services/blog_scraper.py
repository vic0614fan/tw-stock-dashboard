import re
from datetime import datetime, timezone

import feedparser

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(html: str) -> str:
    text = _TAG_RE.sub(" ", html)
    return re.sub(r"\s+", " ", text).strip()


def fetch_blog_posts(feed_url: str, limit: int = 10) -> list[dict]:
    parsed = feedparser.parse(feed_url)

    posts = []
    for entry in parsed.entries[:limit]:
        published_at = None
        if getattr(entry, "published_parsed", None):
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        content = f"{entry.title}\n{_strip_html(entry.get('summary', ''))}"
        posts.append(
            {
                "url": entry.link,
                "published_at": published_at,
                "content": content,
            }
        )
    return posts
