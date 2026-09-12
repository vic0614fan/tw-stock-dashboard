from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import NewsData, NewsStock
from app.schemas import FetchNewsResult, NewsDataOut
from app.services.llm_classifier import LLMNotConfiguredError, classify_news
from app.services.news_fetcher import fetch_all_feeds

router = APIRouter(prefix="/api/news", tags=["news"])

# 標題正規化後相似度超過這個門檻，視為同一則新聞的重複報導，不重複存
_TITLE_SIMILARITY_THRESHOLD = 0.75
_DEDUPE_LOOKBACK_DAYS = 3


def _is_similar_to_existing(title_normalized: str, recent_titles: list[str]) -> bool:
    return any(
        SequenceMatcher(None, title_normalized, existing).ratio() >= _TITLE_SIMILARITY_THRESHOLD
        for existing in recent_titles
    )


@router.post("/fetch", response_model=FetchNewsResult)
def fetch_news(db: Session = Depends(get_db)):
    """抓 RSS 來源 → 標題相似度去重 → LLM 判斷是否個股相關並分類 → 存入資料庫。"""
    items = fetch_all_feeds()

    cutoff = datetime.now(timezone.utc) - timedelta(days=_DEDUPE_LOOKBACK_DAYS)
    recent_titles = [
        row.title_normalized
        for row in db.query(NewsData).filter(NewsData.scraped_at >= cutoff).all()
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

        try:
            result = classify_news(item["title"], item["description"])
        except LLMNotConfiguredError as e:
            raise HTTPException(status_code=500, detail=str(e))

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
        db.flush()  # 取得 news.id 供下面的 NewsStock 使用

        for s in result["stocks"]:
            db.add(NewsStock(news_id=news.id, stock_id=s["stock_id"]))

        recent_titles.append(item["title_normalized"])
        saved += 1

    db.commit()
    return FetchNewsResult(
        items_fetched=len(items),
        items_saved=saved,
        items_skipped_duplicate_url=skipped_duplicate_url,
        items_skipped_similar_title=skipped_similar_title,
        items_skipped_not_stock_relevant=skipped_not_relevant,
    )


@router.get("", response_model=list[NewsDataOut])
def list_news(stock_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(NewsData).options(joinedload(NewsData.stocks))
    if stock_id:
        query = query.join(NewsStock).filter(NewsStock.stock_id == stock_id)
    return query.order_by(NewsData.published_at.desc().nullslast()).all()
