from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.ingest import ingest_industry
from app.schemas import IndustryFetchResult

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.post("/industry/fetch", response_model=IndustryFetchResult)
def fetch_industry(db: Session = Depends(get_db)):
    """向 TWSE 抓上市公司產業別，補到資料庫裡既有的股票上。"""
    updated = ingest_industry(db)
    return IndustryFetchResult(stocks_updated=updated)
