from datetime import datetime, timezone

import feedparser

# YouTube 官方頻道 RSS，不用 API key。缺點是只有影片標題，沒有影片簡介全文，
# LLM 分類的依據比 Threads/部落格薄弱一些
YOUTUBE_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def fetch_youtube_videos(channel_id: str, limit: int = 10) -> list[dict]:
    parsed = feedparser.parse(YOUTUBE_FEED_URL.format(channel_id=channel_id))

    videos = []
    for entry in parsed.entries[:limit]:
        published_at = None
        if getattr(entry, "published_parsed", None):
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        videos.append(
            {
                "url": entry.link,
                "published_at": published_at,
                "content": entry.title,
            }
        )
    return videos
