from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ingest import ingest_shareholding
from app.models import ShareholdingDistribution, Stock
from app.schemas import FetchResult, ShareholdingDistributionOut, ShareholdingDistributionWithNameOut

router = APIRouter(prefix="/api/shareholding", tags=["shareholding"])


@router.post("/fetch", response_model=FetchResult)
def fetch_and_store(db: Session = Depends(get_db)):
    """向 TDCC 抓集保戶股權分散表最新一週資料（無法指定日期，TDCC 只提供最新一週）。"""
    trade_date, saved = ingest_shareholding(db)
    if trade_date is None:
        raise HTTPException(
            status_code=400,
            detail="沒有資料可存：資料庫裡還沒有任何股票（請先抓過資金流向或籌碼面），或 TDCC 沒有回傳資料",
        )

    return FetchResult(date=trade_date, records_saved=saved)


@router.get("", response_model=list[ShareholdingDistributionWithNameOut])
def get_shareholding_by_date(trade_date: date, db: Session = Depends(get_db)):
    rows = (
        db.query(ShareholdingDistribution, Stock.name)
        .join(Stock, ShareholdingDistribution.stock_id == Stock.stock_id)
        .filter(ShareholdingDistribution.date == trade_date)
        .all()
    )
    return [
        ShareholdingDistributionWithNameOut(
            name=name, **ShareholdingDistributionOut.model_validate(s).model_dump()
        )
        for s, name in rows
    ]


@router.get("/{stock_id}", response_model=list[ShareholdingDistributionOut])
def get_shareholding_by_stock(stock_id: str, db: Session = Depends(get_db)):
    """回傳單一股票的歷史大戶持股比例（依日期排序），供趨勢折線圖使用。"""
    rows = (
        db.query(ShareholdingDistribution)
        .filter(ShareholdingDistribution.stock_id == stock_id)
        .order_by(ShareholdingDistribution.date)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"找不到股票代號 {stock_id} 的資料")
    return rows
