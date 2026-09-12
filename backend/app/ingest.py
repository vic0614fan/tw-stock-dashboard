"""抓取外部資料並存入 SQLite 的核心邏輯，供 FastAPI router（手動觸發）和
scheduler（排程自動觸發）共用，避免兩邊各寫一份。
"""

from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models import (
    ChipData,
    Influencer,
    InstitutionalFlow,
    NewsData,
    NewsStock,
    OpinionData,
    OpinionStock,
    ShareholdingDistribution,
    Stock,
)
from app.services.blog_scraper import fetch_blog_posts
from app.services.industry import fetch_industry_map
from app.services.llm_classifier import classify_news, classify_opinion
from app.services.news_fetcher import fetch_all_feeds
from app.services.tdcc import fetch_shareholding_distribution
from app.services.threads_scraper import scrape_threads_posts
from app.services.twse import fetch_institutional_flow, fetch_margin_trading
from app.services.youtube_scraper import fetch_youtube_videos

_TITLE_SIMILARITY_THRESHOLD = 0.75
_DEDUPE_LOOKBACK_DAYS = 3


def ingest_industry(db: Session) -> int:
    """幫資料庫裡已經有的股票補上產業別（只更新既有股票，不會憑空新增股票列）。"""
    industry_map = fetch_industry_map()

    updated = 0
    for stock in db.query(Stock).all():
        industry = industry_map.get(stock.stock_id)
        if industry and stock.industry != industry:
            stock.industry = industry
            updated += 1
    db.commit()
    return updated


def ingest_institutional_flow(db: Session, trade_date: date) -> int:
    """可能拋出 twse.NoTradingDataError，由呼叫端決定怎麼處理。"""
    records = fetch_institutional_flow(trade_date)

    db.query(InstitutionalFlow).filter(InstitutionalFlow.date == trade_date).delete()
    for r in records:
        if not db.get(Stock, r["stock_id"]):
            db.add(Stock(stock_id=r["stock_id"], name=r["name"]))
        db.add(
            InstitutionalFlow(
                stock_id=r["stock_id"],
                date=trade_date,
                foreign_net=r["foreign_net"],
                trust_net=r["trust_net"],
                dealer_net=r["dealer_net"],
                total_net=r["total_net"],
            )
        )
    db.commit()
    return len(records)


def ingest_chip_data(db: Session, trade_date: date) -> int:
    """可能拋出 twse.NoTradingDataError，由呼叫端決定怎麼處理。"""
    records = fetch_margin_trading(trade_date)

    db.query(ChipData).filter(ChipData.date == trade_date).delete()
    for r in records:
        if not db.get(Stock, r["stock_id"]):
            db.add(Stock(stock_id=r["stock_id"], name=r["name"]))
        db.add(
            ChipData(
                stock_id=r["stock_id"],
                date=trade_date,
                margin_buy_balance=r["margin_buy_balance"],
                margin_sell_balance=r["margin_sell_balance"],
            )
        )
    db.commit()
    return len(records)


def ingest_shareholding(db: Session) -> tuple[date | None, int]:
    """回傳 (資料日期, 存了幾筆)；資料庫裡還沒有任何股票或 TDCC 沒資料時回傳 (None, 0)。"""
    known_stock_ids = {row.stock_id for row in db.query(Stock.stock_id).all()}
    if not known_stock_ids:
        return None, 0

    records = fetch_shareholding_distribution(known_stock_ids)
    if not records:
        return None, 0

    trade_date = records[0]["date"]
    db.query(ShareholdingDistribution).filter(ShareholdingDistribution.date == trade_date).delete()
    for r in records:
        db.add(
            ShareholdingDistribution(
                stock_id=r["stock_id"],
                date=r["date"],
                large_holder_ratio=r["large_holder_ratio"],
                large_holder_count=r["large_holder_count"],
                total_holder_count=r["total_holder_count"],
            )
        )
    db.commit()
    return trade_date, len(records)


def _fetch_influencer_posts(influencer: Influencer, limit: int) -> list[dict]:
    """依平台抓貼文/影片/文章，統一整理成 {url, published_at, content} 的格式。"""
    if influencer.platform == "threads":
        return [
            {"url": p["url"], "published_at": p["published_at"], "content": p["content"]}
            for p in scrape_threads_posts(influencer.handle, limit=limit)
        ]
    if influencer.platform == "youtube":
        return fetch_youtube_videos(influencer.handle, limit=limit)
    if influencer.platform == "blog":
        return fetch_blog_posts(influencer.handle, limit=limit)
    raise ValueError(f"不支援的平台：{influencer.platform}")


def ingest_influencer_opinions(db: Session, influencer: Influencer, limit: int = 10) -> dict:
    """可能拋出 llm_classifier.LLMNotConfiguredError。"""
    posts = _fetch_influencer_posts(influencer, limit)

    saved = 0
    skipped_existing = 0
    skipped_not_relevant = 0
    for post in posts:
        if db.query(OpinionData).filter(OpinionData.source_url == post["url"]).first():
            skipped_existing += 1
            continue
        if not post["content"]:
            continue

        result = classify_opinion(post["content"])
        if not result["is_stock_relevant"] or not result["stocks"]:
            skipped_not_relevant += 1
            continue

        opinion = OpinionData(
            influencer_id=influencer.id,
            source_url=post["url"],
            published_at=post["published_at"],
            raw_content=post["content"],
            sentiment=result["sentiment"],
            summary=result["summary"],
        )
        db.add(opinion)
        db.flush()
        for s in result["stocks"]:
            db.add(OpinionStock(opinion_id=opinion.id, stock_id=s["stock_id"]))
        saved += 1

    db.commit()
    return {
        "posts_found": len(posts),
        "opinions_saved": saved,
        "opinions_skipped_existing": skipped_existing,
        "opinions_skipped_not_relevant": skipped_not_relevant,
    }


def _is_similar_to_existing(title_normalized: str, recent_titles: list[str]) -> bool:
    return any(
        SequenceMatcher(None, title_normalized, existing).ratio() >= _TITLE_SIMILARITY_THRESHOLD
        for existing in recent_titles
    )


def ingest_news(db: Session) -> dict:
    """可能拋出 llm_classifier.LLMNotConfiguredError。"""
    items = fetch_all_feeds()

    cutoff = datetime.now(timezone.utc) - timedelta(days=_DEDUPE_LOOKBACK_DAYS)
    recent_titles = [
        row.title_normalized for row in db.query(NewsData).filter(NewsData.scraped_at >= cutoff).all()
    ]

    saved = 0
    skipped_duplicate_url = 0
    skipped_similar_title = 0
    skipped_not_relevant = 0

    for item in items:
        if db.query(NewsData).filter(NewsData.url == item["url"]).first():
            skipped_duplicate_url += 1
            continue
        if _is_similar_to_existing(item["title_normalized"], recent_titles):
            skipped_similar_title += 1
            continue

        result = classify_news(item["title"], item["description"])

        if not result["is_stock_relevant"] or not result["stocks"]:
            skipped_not_relevant += 1
            continue

        news = NewsData(
            source=item["source"],
            title=item["title"],
            title_normalized=item["title_normalized"],
            url=item["url"],
            published_at=item["published_at"],
            summary=result["summary"],
            sentiment=result["sentiment"],
        )
        db.add(news)
        db.flush()
        for s in result["stocks"]:
            db.add(NewsStock(news_id=news.id, stock_id=s["stock_id"]))

        recent_titles.append(item["title_normalized"])
        saved += 1

    db.commit()
    return {
        "items_fetched": len(items),
        "items_saved": saved,
        "items_skipped_duplicate_url": skipped_duplicate_url,
        "items_skipped_similar_title": skipped_similar_title,
        "items_skipped_not_stock_relevant": skipped_not_relevant,
    }
