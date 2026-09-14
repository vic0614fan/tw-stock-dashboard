from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class StockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stock_id: str
    name: str
    industry: str | None


class InstitutionalFlowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stock_id: str
    date: date
    foreign_net: int
    trust_net: int
    dealer_net: int
    total_net: int


class InstitutionalFlowWithNameOut(InstitutionalFlowOut):
    name: str


class ChipDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stock_id: str
    date: date
    margin_buy_balance: int
    margin_sell_balance: int


class ChipDataWithNameOut(ChipDataOut):
    name: str


class FetchResult(BaseModel):
    date: date
    records_saved: int


class ShareholdingDistributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stock_id: str
    date: date
    large_holder_ratio: float
    large_holder_count: int
    total_holder_count: int


class ShareholdingDistributionWithNameOut(ShareholdingDistributionOut):
    name: str


class InfluencerCreate(BaseModel):
    name: str
    platform: str
    handle: str
    profile_url: str
    category: str | None = None


class InfluencerOut(InfluencerCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class OpinionStockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stock_id: str


class OpinionDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    influencer_id: int
    source_url: str
    published_at: datetime | None
    scraped_at: datetime
    raw_content: str
    sentiment: str
    summary: str
    stocks: list[OpinionStockOut]


class OpinionDataWithInfluencerOut(OpinionDataOut):
    influencer_name: str


class ScrapeResult(BaseModel):
    posts_found: int
    opinions_saved: int
    opinions_skipped_existing: int
    opinions_skipped_not_relevant: int


class NewsStockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stock_id: str


class NewsDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    title: str
    url: str
    published_at: datetime | None
    scraped_at: datetime
    summary: str
    sentiment: str
    stocks: list[NewsStockOut]


class FetchNewsResult(BaseModel):
    items_fetched: int
    items_saved: int
    items_skipped_duplicate_url: int
    items_skipped_similar_title: int
    items_skipped_not_stock_relevant: int


class IndustryFetchResult(BaseModel):
    stocks_updated: int


class IndustrySentimentOut(BaseModel):
    industry: str
    bullish: int
    bearish: int
    neutral: int
    total: int


class StockSentimentOut(BaseModel):
    stock_id: str
    stock_name: str | None
    industry: str | None
    bullish: int
    bearish: int
    neutral: int
    total: int
    has_divergence: bool  # 同時有人看多又有人看空


class IndustryFlowOut(BaseModel):
    industry: str
    foreign_net_lots: int  # 外資買賣超（張）
    trust_net_lots: int  # 投信買賣超（張）
    dealer_net_lots: int  # 自營商買賣超（張）
    total_net_lots: int  # 三大法人合計買賣超（張）


class IndustryFlowSummaryOut(BaseModel):
    window_days: int
    trading_dates: list[date]  # 實際有資料、被納入統計的交易日
    generated_at: datetime
    industries: list[IndustryFlowOut]


class ShareholdingFlowOut(BaseModel):
    industry: str
    avg_ratio: float  # 該產業目前大戶持股比例平均值 (%)
    avg_change: float | None  # 跟前一週比較的平均變化（百分點），只有兩週以上資料才有值


class ShareholdingFlowSummaryOut(BaseModel):
    mode: str  # "level"（只有一週資料，顯示目前比例）或 "change"（兩週以上，顯示週對週變化）
    latest_date: date | None
    previous_date: date | None
    generated_at: datetime
    industries: list[ShareholdingFlowOut]


class ConsensusItemOut(BaseModel):
    type: str  # "opinion" 或 "news"
    source: str  # 意見領袖名字或新聞來源
    sentiment: str
    summary: str
    stock_id: str | None
    stock_name: str | None
    industry: str | None
    published_at: datetime | None
    url: str


class LastUpdatedOut(BaseModel):
    # 資金流向/籌碼面/大戶持股本來就是「日」為單位的資料，用 date 而不是 datetime，
    # 避免前端顯示出一個假的「00:00」時間，看起來像是半夜更新的
    institutional_flow: date | None
    chip_data: date | None
    shareholding: date | None
    opinions: datetime | None
    news: datetime | None


class ConsensusSummaryOut(BaseModel):
    window_days: int
    generated_at: datetime
    last_updated: LastUpdatedOut
    industry_sentiment: list[IndustrySentimentOut]
    stock_sentiment: list[StockSentimentOut]
    recent_items: list[ConsensusItemOut]


class StockConsensusOut(BaseModel):
    window_days: int
    generated_at: datetime
    summary: StockSentimentOut | None
    items: list[ConsensusItemOut]


class TimelineOpinionOut(BaseModel):
    sentiment: str
    summary: str
    published_at: datetime | None
    url: str
    trend: str | None  # None（第一次講這檔）｜"延續"｜"反轉"


class StockTimelineOut(BaseModel):
    stock_id: str
    stock_name: str | None
    opinions: list[TimelineOpinionOut]  # 依時間排序，舊到新


class InfluencerTimelineOut(BaseModel):
    influencer: InfluencerOut
    stocks: list[StockTimelineOut]
