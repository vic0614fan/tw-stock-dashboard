from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.ingest import ingest_influencer_opinions
from app.models import Influencer, OpinionData, OpinionStock, Stock
from app.schemas import (
    InfluencerCreate,
    InfluencerOut,
    InfluencerTimelineOut,
    OpinionDataOut,
    ScrapeResult,
    StockTimelineOut,
    TimelineOpinionOut,
)
from app.services.llm_classifier import LLMNotConfiguredError

_BULLISH = {"多", "正面"}
_BEARISH = {"空", "負面"}
_EPOCH = datetime.min


def _bucket(sentiment: str) -> str:
    if sentiment in _BULLISH:
        return "bullish"
    if sentiment in _BEARISH:
        return "bearish"
    return "neutral"

router = APIRouter(prefix="/api/influencers", tags=["influencers"])


@router.get("", response_model=list[InfluencerOut])
def list_influencers(db: Session = Depends(get_db)):
    return db.query(Influencer).all()


@router.post("", response_model=InfluencerOut)
def create_influencer(payload: InfluencerCreate, db: Session = Depends(get_db)):
    influencer = Influencer(**payload.model_dump())
    db.add(influencer)
    db.commit()
    db.refresh(influencer)
    return influencer


@router.post("/{influencer_id}/scrape", response_model=ScrapeResult)
def scrape_influencer(influencer_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """抓該意見領袖最近的貼文、丟 LLM 分類，新貼文才會存入資料庫（已存在的用 source_url 跳過）。"""
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail=f"找不到 influencer id={influencer_id}")
    if influencer.platform not in ("threads", "youtube", "blog"):
        raise HTTPException(status_code=400, detail=f"不支援的平台：{influencer.platform}")

    try:
        result = ingest_influencer_opinions(db, influencer, limit=limit)
    except LLMNotConfiguredError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ScrapeResult(**result)


@router.get("/{influencer_id}/opinions", response_model=list[OpinionDataOut])
def get_influencer_opinions(influencer_id: int, db: Session = Depends(get_db)):
    return (
        db.query(OpinionData)
        .options(joinedload(OpinionData.stocks))
        .filter(OpinionData.influencer_id == influencer_id)
        .order_by(OpinionData.published_at.desc().nullslast())
        .all()
    )


@router.get("/{influencer_id}/timeline", response_model=InfluencerTimelineOut)
def get_influencer_timeline(influencer_id: int, db: Session = Depends(get_db)):
    """這位意見領袖的完整發言紀錄，依股票分組、依時間排序，並標記每次發言是「延續」
    還是「反轉」前一次對同一檔股票的立場——用於意見領袖個人頁。
    """
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail=f"找不到 influencer id={influencer_id}")

    rows = (
        db.query(OpinionData, OpinionStock.stock_id, Stock.name)
        .join(OpinionStock, OpinionStock.opinion_id == OpinionData.id)
        .outerjoin(Stock, Stock.stock_id == OpinionStock.stock_id)
        .filter(OpinionData.influencer_id == influencer_id)
        .all()
    )

    by_stock: dict[str, dict] = {}
    for opinion, stock_id, stock_name in rows:
        entry = by_stock.setdefault(stock_id, {"stock_name": stock_name, "opinions": []})
        entry["opinions"].append(opinion)

    stocks = []
    for stock_id, entry in by_stock.items():
        ordered = sorted(entry["opinions"], key=lambda o: o.published_at or o.scraped_at or _EPOCH)
        timeline_opinions = []
        prev_bucket = None
        for o in ordered:
            trend = None
            if prev_bucket is not None:
                trend = "延續" if _bucket(o.sentiment) == prev_bucket else "反轉"
            timeline_opinions.append(
                TimelineOpinionOut(
                    sentiment=o.sentiment,
                    summary=o.summary,
                    published_at=o.published_at or o.scraped_at,
                    url=o.source_url,
                    trend=trend,
                )
            )
            prev_bucket = _bucket(o.sentiment)
        stocks.append(StockTimelineOut(stock_id=stock_id, stock_name=entry["stock_name"], opinions=timeline_opinions))

    stocks.sort(key=lambda s: s.opinions[-1].published_at or _EPOCH, reverse=True)

    return InfluencerTimelineOut(influencer=influencer, stocks=stocks)
