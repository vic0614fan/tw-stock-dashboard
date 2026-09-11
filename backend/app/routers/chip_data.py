from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChipData, Stock
from app.schemas import ChipDataOut, ChipDataWithNameOut, FetchResult
from app.services.twse import NoTradingDataError, fetch_margin_trading

router = APIRouter(prefix="/api/chip-data", tags=["chip-data"])


@router.post("/fetch", response_model=FetchResult)
def fetch_and_store(trade_date: date | None = None, db: Session = Depends(get_db)):
    """向 TWSE 抓取指定日期的融資融券餘額並存入 SQLite。"""
    if trade_date is None:
        trade_date = date.today()
    try:
        records = fetch_margin_trading(trade_date)
    except NoTradingDataError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 該日期若已抓過，先清掉舊資料再重新寫入，確保重複呼叫是安全的
    db.query(ChipData).filter(ChipData.date == trade_date).delete()

    for r in records:
        if not db.get(Stock, r["stock_id"]):
            db.add(Stock(stock_id=r["stock_id"], name=r["name"]))
        db.add(
            ChipData(
                stock_id=r["stock_id"],
                date=trade_date,
                margin_buy_balance=r["margin_buy_balance"],
                margin_sell_balance=r["margin_sell_balance"],
            )
        )
    db.commit()

    return FetchResult(date=trade_date, records_saved=len(records))


@router.get("", response_model=list[ChipDataWithNameOut])
def get_chip_data_by_date(trade_date: date, db: Session = Depends(get_db)):
    """回傳指定日期、所有股票的融資融券餘額。"""
    rows = (
        db.query(ChipData, Stock.name)
        .join(Stock, ChipData.stock_id == Stock.stock_id)
        .filter(ChipData.date == trade_date)
        .all()
    )
    return [
        ChipDataWithNameOut(name=name, **ChipDataOut.model_validate(chip).model_dump())
        for chip, name in rows
    ]


@router.get("/{stock_id}", response_model=list[ChipDataOut])
def get_chip_data_by_stock(stock_id: str, db: Session = Depends(get_db)):
    """回傳單一股票的歷史融資融券餘額（依日期排序），供趨勢折線圖使用。"""
    rows = (
        db.query(ChipData)
        .filter(ChipData.stock_id == stock_id)
        .order_by(ChipData.date)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"找不到股票代號 {stock_id} 的資料")
    return rows
