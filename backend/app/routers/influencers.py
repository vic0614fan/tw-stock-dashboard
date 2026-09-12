from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.ingest import ingest_influencer_opinions
from app.models import Influencer, OpinionData
from app.schemas import InfluencerCreate, InfluencerOut, OpinionDataOut, ScrapeResult
from app.services.llm_classifier import LLMNotConfiguredError

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
