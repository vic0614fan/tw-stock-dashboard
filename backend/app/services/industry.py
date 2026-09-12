import requests

TWSE_COMPANY_INFO_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"

HEADERS = {"User-Agent": "Mozilla/5.0"}

# 對照 TWSE 官方「上市證券之產業別」清單（isin.twse.com.tw/isin/class_i.jsp?kind=1），
# 07、34 這兩個代碼官方本來就沒有用（歷史上併掉了），不是漏抓
INDUSTRY_CODE_MAP = {
    "01": "水泥工業", "02": "食品工業", "03": "塑膠工業", "04": "紡織纖維",
    "05": "電機機械", "06": "電器電纜", "08": "玻璃陶瓷", "09": "造紙工業",
    "10": "鋼鐵工業", "11": "橡膠工業", "12": "汽車工業", "13": "電子工業",
    "14": "建材營造業", "15": "航運業", "16": "觀光餐旅", "17": "金融保險業",
    "18": "貿易百貨業", "19": "綜合", "20": "其他業", "21": "化學工業",
    "22": "生技醫療業", "23": "油電燃氣業", "24": "半導體業", "25": "電腦及週邊設備業",
    "26": "光電業", "27": "通信網路業", "28": "電子零組件業", "29": "電子通路業",
    "30": "資訊服務業", "31": "其他電子業", "32": "文化創意業", "33": "農業科技業",
    "35": "綠能環保", "36": "數位雲端", "37": "運動休閒", "38": "居家生活",
}


def fetch_industry_map() -> dict[str, str]:
    """回傳 {股票代號: 產業名稱}。"""
    resp = requests.get(TWSE_COMPANY_INFO_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    companies = resp.json()

    result = {}
    for c in companies:
        stock_id = c["公司代號"].strip()
        code = c["產業別"].strip()
        if code in INDUSTRY_CODE_MAP:
            result[stock_id] = INDUSTRY_CODE_MAP[code]
    return result
