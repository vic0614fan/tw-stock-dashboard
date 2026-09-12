from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.ingest import ingest_news
from app.models import NewsData, NewsStock
from app.schemas import FetchNewsResult, NewsDataOut
from app.services.llm_classifier import LLMNotConfiguredError

router = APIRouter(prefix="/api/news", tags=["news"])


@router.post("/fetch", response_model=FetchNewsResult)
def fetch_news(db: Session = Depends(get_db)):
    """抓 RSS 來源 → 標題相似度去重 → LLM 判斷是否個股相關並分類 → 存入資料庫。"""
    try:
        result = ingest_news(db)
    except LLMNotConfiguredError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FetchNewsResult(**result)


@router.get("", response_model=list[NewsDataOut])
def list_news(stock_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(NewsData).options(joinedload(NewsData.stocks))
    if stock_id:
        query = query.join(NewsStock).filter(NewsStock.stock_id == stock_id)
    return query.order_by(NewsData.published_at.desc().nullslast()).all()
