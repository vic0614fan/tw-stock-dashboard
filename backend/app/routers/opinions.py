from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import OpinionData, OpinionStock
from app.schemas import OpinionDataWithInfluencerOut

router = APIRouter(prefix="/api/opinions", tags=["opinions"])


@router.get("", response_model=list[OpinionDataWithInfluencerOut])
def list_opinions(stock_id: str | None = None, influencer_id: int | None = None, db: Session = Depends(get_db)):
    """查詢意見資料，可用股票代號（跨意見領袖）或 influencer_id 篩選，用於看「某檔股票的意見隨時間變化」。"""
    query = db.query(OpinionData).options(joinedload(OpinionData.stocks), joinedload(OpinionData.influencer))
    if stock_id:
        query = query.join(OpinionStock).filter(OpinionStock.stock_id == stock_id)
    if influencer_id:
        query = query.filter(OpinionData.influencer_id == influencer_id)
    rows = query.order_by(OpinionData.published_at.desc().nullslast()).all()
    return [
        OpinionDataWithInfluencerOut(
            influencer_name=o.influencer.name,
            **{
                "id": o.id,
                "influencer_id": o.influencer_id,
                "source_url": o.source_url,
                "published_at": o.published_at,
                "scraped_at": o.scraped_at,
                "raw_content": o.raw_content,
                "sentiment": o.sentiment,
                "summary": o.summary,
                "stocks": o.stocks,
            },
        )
        for o in rows
    ]
