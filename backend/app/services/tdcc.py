import csv
import io
from datetime import date, datetime

import requests

# TDCC 集保戶股權分散表開放資料，每週更新，只會回傳「最新一週」的快照（無法查歷史日期），
# 所以要靠我們自己排程每週抓一次、累積存進資料庫才能看出歷史趨勢
TDCC_URL = "https://opendata.tdcc.com.tw/getOD.ashx?id=1-5"

HEADERS = {"User-Agent": "Mozilla/5.0"}

# 持股分級代碼是固定的 17 級距（實測 TDCC 官網查詢頁面比對出來的，代碼 16 官網不會顯示、永遠是 0，
# 是保留欄位；17 才是「合計」列，不是官網序號最後的 16）
LARGE_HOLDER_LEVEL = "15"  # 1,000,001股（即1,000張）以上
TOTAL_LEVEL = "17"  # 合計


def fetch_shareholding_distribution(known_stock_ids: set[str]) -> list[dict]:
    """抓 TDCC 集保戶股權分散表最新一週資料，只保留 known_stock_ids 裡有的股票代號
    （TDCC 原始資料還包含權證、受益證券等我們不需要的證券類型）。
    """
    resp = requests.get(TDCC_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    reader = csv.DictReader(io.StringIO(resp.content.decode("utf-8-sig")))

    by_stock: dict[str, dict[str, dict]] = {}
    trade_date = None
    for row in reader:
        stock_id = row["證券代號"].strip()
        if stock_id not in known_stock_ids:
            continue
        level = row["持股分級"].strip()
        if level not in (LARGE_HOLDER_LEVEL, TOTAL_LEVEL):
            continue

        if trade_date is None:
            trade_date = datetime.strptime(row["資料日期"].strip(), "%Y%m%d").date()

        by_stock.setdefault(stock_id, {})[level] = {
            "count": int(row["人數"]),
            "ratio": float(row["占集保庫存數比例%"]),
        }

    records = []
    for stock_id, levels in by_stock.items():
        if LARGE_HOLDER_LEVEL not in levels or TOTAL_LEVEL not in levels:
            continue
        records.append(
            {
                "stock_id": stock_id,
                "date": trade_date,
                "large_holder_ratio": levels[LARGE_HOLDER_LEVEL]["ratio"],
                "large_holder_count": levels[LARGE_HOLDER_LEVEL]["count"],
                "total_holder_count": levels[TOTAL_LEVEL]["count"],
            }
        )
    return records
