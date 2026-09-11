from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InstitutionalFlow, Stock
from app.schemas import FetchResult, InstitutionalFlowOut, InstitutionalFlowWithNameOut
from app.services.twse import NoTradingDataError, fetch_institutional_flow

router = APIRouter(prefix="/api/institutional-flow", tags=["institutional-flow"])


@router.post("/fetch", response_model=FetchResult)
def fetch_and_store(trade_date: date | None = None, db: Session = Depends(get_db)):
    """向 TWSE 抓取指定日期的三大法人買賣超資料並存入 SQLite。"""
    if trade_date is None:
        trade_date = date.today()
    try:
        records = fetch_institutional_flow(trade_date)
    except NoTradingDataError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 該日期若已抓過，先清掉舊資料再重新寫入，確保重複呼叫是安全的
    db.query(InstitutionalFlow).filter(InstitutionalFlow.date == trade_date).delete()

    for r in records:
        if not db.get(Stock, r["stock_id"]):
            db.add(Stock(stock_id=r["stock_id"], name=r["name"]))
        db.add(
            InstitutionalFlow(
                stock_id=r["stock_id"],
                date=trade_date,
                foreign_net=r["foreign_net"],
                trust_net=r["trust_net"],
                dealer_net=r["dealer_net"],
                total_net=r["total_net"],
            )
        )
    db.commit()

    return FetchResult(date=trade_date, records_saved=len(records))


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
