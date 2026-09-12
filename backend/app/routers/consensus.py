from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    ChipData,
    InstitutionalFlow,
    NewsData,
    NewsStock,
    OpinionData,
    OpinionStock,
    ShareholdingDistribution,
    Stock,
)
from app.schemas import ConsensusItemOut, ConsensusSummaryOut, IndustrySentimentOut, LastUpdatedOut

router = APIRouter(prefix="/api/consensus", tags=["consensus"])

# 「多」跟「正面」都算看多、「空」跟「負面」都算看空——意見領袖跟新聞用的是不同詞彙，
# 統計「今日多空共識」時要先統一成同一套
_BULLISH = {"多", "正面"}
_BEARISH = {"空", "負面"}

# 專案裡的 datetime 欄位都是不帶時區資訊的（存進 SQLite 前就統一轉過），這裡也一律用
# naive datetime 處理，避免跟資料庫讀出來的值比較/排序時 aware/naive 對不上而噴錯
_EPOCH = datetime.min


def _bucket(sentiment: str) -> str:
    if sentiment in _BULLISH:
        return "bullish"
    if sentiment in _BEARISH:
        return "bearish"
    return "neutral"


def _date_to_datetime(d: date | None) -> datetime | None:
    if d is None:
        return None
    return datetime.combine(d, time.min)


@router.get("", response_model=ConsensusSummaryOut)
def get_consensus(
    window_days: int = Query(7, ge=1, le=30, description="統計最近幾天的意見/新聞"),
    db: Session = Depends(get_db),
):
    """「今日多空共識」摘要：依產業統計最近意見領袖/新聞的多空分布，供首頁一眼看出用。

    因為意見領袖/新聞不是每天都有新內容，這裡用「最近 N 天」的滾動視窗，不是嚴格只看今天，
    避免某天剛好沒人發文就整頁空白。
    """
    cutoff = datetime.utcnow() - timedelta(days=window_days)

    opinion_rows = (
        db.query(OpinionData, OpinionStock.stock_id, Stock.name, Stock.industry)
        .join(OpinionStock, OpinionStock.opinion_id == OpinionData.id)
        .outerjoin(Stock, Stock.stock_id == OpinionStock.stock_id)
        .join(OpinionData.influencer)
        .filter(func.coalesce(OpinionData.published_at, OpinionData.scraped_at) >= cutoff)
        .all()
    )

    news_rows = (
        db.query(NewsData, NewsStock.stock_id, Stock.name, Stock.industry)
        .join(NewsStock, NewsStock.news_id == NewsData.id)
        .outerjoin(Stock, Stock.stock_id == NewsStock.stock_id)
        .filter(func.coalesce(NewsData.published_at, NewsData.scraped_at) >= cutoff)
        .all()
    )

    items: list[ConsensusItemOut] = []
    for opinion, stock_id, stock_name, industry in opinion_rows:
        items.append(
            ConsensusItemOut(
                type="opinion",
                source=opinion.influencer.name,
                sentiment=opinion.sentiment,
                summary=opinion.summary,
                stock_id=stock_id,
                stock_name=stock_name,
                industry=industry,
                published_at=opinion.published_at or opinion.scraped_at,
                url=opinion.source_url,
            )
        )
    for news, stock_id, stock_name, industry in news_rows:
        items.append(
            ConsensusItemOut(
                type="news",
                source=news.source,
                sentiment=news.sentiment,
                summary=news.summary,
                stock_id=stock_id,
                stock_name=stock_name,
                industry=industry,
                published_at=news.published_at or news.scraped_at,
                url=news.url,
            )
        )

    industry_counts: dict[str, dict[str, int]] = {}
    for item in items:
        if not item.industry:
            continue
        bucket = industry_counts.setdefault(item.industry, {"bullish": 0, "bearish": 0, "neutral": 0})
        bucket[_bucket(item.sentiment)] += 1

    industry_sentiment = [
        IndustrySentimentOut(
            industry=industry,
            bullish=counts["bullish"],
            bearish=counts["bearish"],
            neutral=counts["neutral"],
            total=counts["bullish"] + counts["bearish"] + counts["neutral"],
        )
        for industry, counts in industry_counts.items()
    ]
    industry_sentiment.sort(key=lambda x: x.total, reverse=True)

    items.sort(key=lambda x: x.published_at or _EPOCH, reverse=True)

    def _max(model, col):
        return db.query(func.max(col)).select_from(model).scalar()

    last_updated = LastUpdatedOut(
        institutional_flow=_date_to_datetime(_max(InstitutionalFlow, InstitutionalFlow.date)),
        chip_data=_date_to_datetime(_max(ChipData, ChipData.date)),
        shareholding=_date_to_datetime(_max(ShareholdingDistribution, ShareholdingDistribution.date)),
        opinions=_max(OpinionData, OpinionData.scraped_at),
        news=_max(NewsData, NewsData.scraped_at),
    )

    return ConsensusSummaryOut(
        window_days=window_days,
        generated_at=datetime.utcnow(),
        last_updated=last_updated,
        industry_sentiment=industry_sentiment,
        recent_items=items[:20],
    )
