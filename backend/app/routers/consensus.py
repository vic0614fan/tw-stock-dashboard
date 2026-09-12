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
from app.schemas import (
    ConsensusItemOut,
    ConsensusSummaryOut,
    IndustrySentimentOut,
    LastUpdatedOut,
    StockConsensusOut,
    StockSentimentOut,
)

router = APIRouter(prefix="/api/consensus", tags=["consensus"])

# 「多」跟「正面」都算看多、「空」跟「負面」都算看空——意見領袖跟新聞用的是不同詞彙，
# 統計多空共識時要先統一成同一套
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


def _collect_items(db: Session, cutoff: datetime, stock_id: str | None = None) -> list[ConsensusItemOut]:
    """撈最近意見領袖/新聞，統一整理成 ConsensusItemOut。stock_id 給定時只抓那一檔股票的。"""
    opinion_query = (
        db.query(OpinionData, OpinionStock.stock_id, Stock.name, Stock.industry)
        .join(OpinionStock, OpinionStock.opinion_id == OpinionData.id)
        .outerjoin(Stock, Stock.stock_id == OpinionStock.stock_id)
        .join(OpinionData.influencer)
        .filter(func.coalesce(OpinionData.published_at, OpinionData.scraped_at) >= cutoff)
    )
    news_query = (
        db.query(NewsData, NewsStock.stock_id, Stock.name, Stock.industry)
        .join(NewsStock, NewsStock.news_id == NewsData.id)
        .outerjoin(Stock, Stock.stock_id == NewsStock.stock_id)
        .filter(func.coalesce(NewsData.published_at, NewsData.scraped_at) >= cutoff)
    )
    if stock_id:
        opinion_query = opinion_query.filter(OpinionStock.stock_id == stock_id)
        news_query = news_query.filter(NewsStock.stock_id == stock_id)

    items: list[ConsensusItemOut] = []
    for opinion, s_id, stock_name, industry in opinion_query.all():
        items.append(
            ConsensusItemOut(
                type="opinion",
                source=opinion.influencer.name,
                sentiment=opinion.sentiment,
                summary=opinion.summary,
                stock_id=s_id,
                stock_name=stock_name,
                industry=industry,
                published_at=opinion.published_at or opinion.scraped_at,
                url=opinion.source_url,
            )
        )
    for news, s_id, stock_name, industry in news_query.all():
        items.append(
            ConsensusItemOut(
                type="news",
                source=news.source,
                sentiment=news.sentiment,
                summary=news.summary,
                stock_id=s_id,
                stock_name=stock_name,
                industry=industry,
                published_at=news.published_at or news.scraped_at,
                url=news.url,
            )
        )

    items.sort(key=lambda x: x.published_at or _EPOCH, reverse=True)
    return items


def _aggregate(items: list[ConsensusItemOut], key_fn, name_fn) -> dict:
    """依 key_fn(item) 分組統計多空，key 為 None 的項目跳過。"""
    counts: dict = {}
    for item in items:
        key = key_fn(item)
        if not key:
            continue
        bucket = counts.setdefault(key, {"bullish": 0, "bearish": 0, "neutral": 0, "meta": name_fn(item)})
        bucket[_bucket(item.sentiment)] += 1
    return counts


@router.get("", response_model=ConsensusSummaryOut)
def get_consensus(
    window_days: int = Query(7, ge=1, le=30, description="統計最近幾天的意見/新聞"),
    db: Session = Depends(get_db),
):
    """首頁用的「今日多空共識」摘要：依產業、依個股統計最近意見領袖/新聞的多空分布。

    因為意見領袖/新聞不是每天都有新內容，這裡用「最近 N 天」的滾動視窗，不是嚴格只看今天，
    避免某天剛好沒人發文就整頁空白。
    """
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    items = _collect_items(db, cutoff)

    industry_counts = _aggregate(items, lambda i: i.industry, lambda i: None)
    industry_sentiment = [
        IndustrySentimentOut(
            industry=industry,
            bullish=c["bullish"],
            bearish=c["bearish"],
            neutral=c["neutral"],
            total=c["bullish"] + c["bearish"] + c["neutral"],
        )
        for industry, c in industry_counts.items()
    ]
    industry_sentiment.sort(key=lambda x: x.total, reverse=True)

    stock_counts = _aggregate(items, lambda i: i.stock_id, lambda i: (i.stock_name, i.industry))
    stock_sentiment = [
        StockSentimentOut(
            stock_id=stock_id,
            stock_name=c["meta"][0],
            industry=c["meta"][1],
            bullish=c["bullish"],
            bearish=c["bearish"],
            neutral=c["neutral"],
            total=c["bullish"] + c["bearish"] + c["neutral"],
            has_divergence=c["bullish"] > 0 and c["bearish"] > 0,
        )
        for stock_id, c in stock_counts.items()
    ]
    stock_sentiment.sort(key=lambda x: x.total, reverse=True)

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
        stock_sentiment=stock_sentiment[:15],
        recent_items=items[:20],
    )


@router.get("/stock/{stock_id}", response_model=StockConsensusOut)
def get_stock_consensus(
    stock_id: str,
    window_days: int = Query(30, ge=1, le=90, description="統計最近幾天的意見/新聞"),
    db: Session = Depends(get_db),
):
    """單一股票的多空共識摘要，供「查詢單一股票細節」頁面最上方的摘要卡片用。"""
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    items = _collect_items(db, cutoff, stock_id=stock_id)

    summary = None
    if items:
        bullish = sum(1 for i in items if _bucket(i.sentiment) == "bullish")
        bearish = sum(1 for i in items if _bucket(i.sentiment) == "bearish")
        neutral = sum(1 for i in items if _bucket(i.sentiment) == "neutral")
        summary = StockSentimentOut(
            stock_id=stock_id,
            stock_name=items[0].stock_name,
            industry=items[0].industry,
            bullish=bullish,
            bearish=bearish,
            neutral=neutral,
            total=bullish + bearish + neutral,
            has_divergence=bullish > 0 and bearish > 0,
        )

    return StockConsensusOut(
        window_days=window_days,
        generated_at=datetime.utcnow(),
        summary=summary,
        items=items,
    )
