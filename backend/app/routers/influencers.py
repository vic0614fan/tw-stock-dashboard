from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Influencer, OpinionData, OpinionStock
from app.schemas import InfluencerCreate, InfluencerOut, OpinionDataOut, ScrapeResult
from app.services.llm_classifier import LLMNotConfiguredError, classify_opinion
from app.services.threads_scraper import scrape_threads_posts

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
    if influencer.platform != "threads":
        raise HTTPException(status_code=400, detail=f"目前只支援 threads，這位是 {influencer.platform}")

    posts = scrape_threads_posts(influencer.handle, limit=limit)

    saved = 0
    skipped = 0
    for post in posts:
        if db.query(OpinionData).filter(OpinionData.source_url == post["url"]).first():
            skipped += 1
            continue
        if not post["content"]:
            continue

        try:
            result = classify_opinion(post["content"])
        except LLMNotConfiguredError as e:
            raise HTTPException(status_code=500, detail=str(e))

        opinion = OpinionData(
            influencer_id=influencer.id,
            source_url=post["url"],
            published_at=post["published_at"],
            raw_content=post["content"],
            sentiment=result["sentiment"],
            summary=result["summary"],
        )
        db.add(opinion)
        db.flush()  # 取得 opinion.id 供下面的 OpinionStock 使用

        for s in result["stocks"]:
            db.add(OpinionStock(opinion_id=opinion.id, stock_id=s["stock_id"]))

        saved += 1

    db.commit()
    return ScrapeResult(posts_found=len(posts), opinions_saved=saved, opinions_skipped_existing=skipped)


@router.get("/{influencer_id}/opinions", response_model=list[OpinionDataOut])
def get_influencer_opinions(influencer_id: int, db: Session = Depends(get_db)):
    return (
        db.query(OpinionData)
        .options(joinedload(OpinionData.stocks))
        .filter(OpinionData.influencer_id == influencer_id)
        .order_by(OpinionData.published_at.desc().nullslast())
        .all()
    )
