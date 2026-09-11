from datetime import date

import requests

T86_URL = "https://www.twse.com.tw/rwd/zh/fund/T86"
MI_MARGN_URL = "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN"

HEADERS = {"User-Agent": "Mozilla/5.0"}

# MI_MARGN「融資融券彙總」表的欄位是固定位置（買進/賣出/前日餘額/今日餘額 在融資、融券
# 兩邊都重複出現，無法像 T86 用欄位名稱對應），用這個清單在解析前先比對，格式一變就直接報錯
MARGIN_TABLE_FIELDS = [
    "代號", "名稱", "買進", "賣出", "現金償還", "前日餘額", "今日餘額", "次一營業日限額",
    "買進", "賣出", "現券償還", "前日餘額", "今日餘額", "次一營業日限額", "資券互抵", "註記",
]
MARGIN_STOCK_ID_IDX = 0
MARGIN_NAME_IDX = 1
MARGIN_BUY_BALANCE_IDX = 6  # 融資今日餘額
MARGIN_SELL_BALANCE_IDX = 12  # 融券今日餘額

# TWSE 欄位名稱 -> 我們資料庫欄位名稱
FIELD_MAP = {
    "證券代號": "stock_id",
    "證券名稱": "name",
    "外陸資買賣超股數(不含外資自營商)": "foreign_dealer_free_net",
    "外資自營商買賣超股數": "foreign_dealer_net",
    "投信買賣超股數": "trust_net",
    "自營商買賣超股數": "dealer_net",
    "三大法人買賣超股數": "total_net",
}


class NoTradingDataError(Exception):
    """該日期非交易日，或 TWSE 尚未公布資料。"""


def _to_int(value: str) -> int:
    return int(value.replace(",", ""))


def fetch_institutional_flow(trade_date: date) -> list[dict]:
    """向 TWSE OpenAPI (T86) 抓取指定日期的三大法人買賣超資料。"""
    # ALLBUT0999 = 全部(不含權證、牛熊證、可展延牛熊證)，避免把上萬檔權證也存進資料庫
    params = {"response": "json", "date": trade_date.strftime("%Y%m%d"), "selectType": "ALLBUT0999"}
    resp = requests.get(T86_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    payload = resp.json()

    if payload.get("stat") != "OK":
        raise NoTradingDataError(f"{trade_date} 無資料（非交易日或尚未公布）：{payload.get('stat')}")

    fields = payload["fields"]
    col_index = {FIELD_MAP[name]: idx for idx, name in enumerate(fields) if name in FIELD_MAP}

    records = []
    for row in payload["data"]:
        foreign_net = _to_int(row[col_index["foreign_dealer_free_net"]]) + _to_int(
            row[col_index["foreign_dealer_net"]]
        )
        records.append(
            {
                "stock_id": row[col_index["stock_id"]].strip(),
                "name": row[col_index["name"]].strip(),
                "foreign_net": foreign_net,
                "trust_net": _to_int(row[col_index["trust_net"]]),
                "dealer_net": _to_int(row[col_index["dealer_net"]]),
                "total_net": _to_int(row[col_index["total_net"]]),
            }
        )
    return records


def fetch_margin_trading(trade_date: date) -> list[dict]:
    """向 TWSE OpenAPI (MI_MARGN) 抓取指定日期個股融資融券餘額。"""
    params = {"response": "json", "date": trade_date.strftime("%Y%m%d"), "selectType": "ALL"}
    resp = requests.get(MI_MARGN_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    payload = resp.json()

    if payload.get("stat") != "OK":
        raise NoTradingDataError(f"{trade_date} 無資料（非交易日或尚未公布）：{payload.get('stat')}")

    table = next((t for t in payload["tables"] if "融資融券彙總" in t.get("title", "")), None)
    if table is None:
        raise ValueError("MI_MARGN 回傳格式異常：找不到「融資融券彙總」表")
    if table["fields"] != MARGIN_TABLE_FIELDS:
        raise ValueError(f"MI_MARGN 欄位格式已變動，需更新解析邏輯：{table['fields']}")

    records = []
    for row in table["data"]:
        records.append(
            {
                "stock_id": row[MARGIN_STOCK_ID_IDX].strip(),
                "name": row[MARGIN_NAME_IDX].strip(),
                "margin_buy_balance": _to_int(row[MARGIN_BUY_BALANCE_IDX]),
                "margin_sell_balance": _to_int(row[MARGIN_SELL_BALANCE_IDX]),
            }
        )
    return records
