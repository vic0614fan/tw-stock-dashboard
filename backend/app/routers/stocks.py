from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.ingest import ingest_industry
from app.models import Stock
from app.schemas import IndustryFetchResult, StockOut

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("", response_model=list[StockOut])
def list_stocks(industry: str | None = None, db: Session = Depends(get_db)):
    """列出股票主檔，可用 industry 篩選同產業的所有股票——供「點產業看類股列表」用。"""
    query = db.query(Stock)
    if industry:
        query = query.filter(Stock.industry == industry)
    return query.order_by(Stock.stock_id).all()


@router.post("/industry/fetch", response_model=IndustryFetchResult)
def fetch_industry(db: Session = Depends(get_db)):
    """向 TWSE 抓上市公司產業別，補到資料庫裡既有的股票上。"""
    updated = ingest_industry(db)
    return IndustryFetchResult(stocks_updated=updated)
