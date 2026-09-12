from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ingest import ingest_institutional_flow
from app.models import InstitutionalFlow, Stock
from app.schemas import FetchResult, InstitutionalFlowOut, InstitutionalFlowWithNameOut
from app.services.twse import NoTradingDataError

router = APIRouter(prefix="/api/institutional-flow", tags=["institutional-flow"])


@router.post("/fetch", response_model=FetchResult)
def fetch_and_store(trade_date: date | None = None, db: Session = Depends(get_db)):
    """向 TWSE 抓取指定日期的三大法人買賣超資料並存入 SQLite。"""
    if trade_date is None:
        trade_date = date.today()
    try:
        saved = ingest_institutional_flow(db, trade_date)
    except NoTradingDataError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return FetchResult(date=trade_date, records_saved=saved)


@router.get("", response_model=list[InstitutionalFlowWithNameOut])
def get_flow_by_date(trade_date: date, db: Session = Depends(get_db)):
    """回傳指定日期、所有股票的三大法人買賣超資料。"""
    rows = (
        db.query(InstitutionalFlow, Stock.name)
        .join(Stock, InstitutionalFlow.stock_id == Stock.stock_id)
        .filter(InstitutionalFlow.date == trade_date)
        .all()
    )
    return [
        InstitutionalFlowWithNameOut(name=name, **InstitutionalFlowOut.model_validate(flow).model_dump())
        for flow, name in rows
    ]


@router.get("/{stock_id}", response_model=list[InstitutionalFlowOut])
def get_flow_by_stock(stock_id: str, db: Session = Depends(get_db)):
    """回傳單一股票的歷史三大法人買賣超資料（依日期排序），供折線／堆疊長條圖使用。"""
    rows = (
        db.query(InstitutionalFlow)
        .filter(InstitutionalFlow.stock_id == stock_id)
        .order_by(InstitutionalFlow.date)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"找不到股票代號 {stock_id} 的資料")
    return rows
