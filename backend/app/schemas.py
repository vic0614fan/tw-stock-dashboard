from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


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
    institutional_flow: datetime | None
    chip_data: datetime | None
    shareholding: datetime | None
    opinions: datetime | None
    news: datetime | None


class ConsensusSummaryOut(BaseModel):
    window_days: int
    generated_at: datetime
    last_updated: LastUpdatedOut
    industry_sentiment: list[IndustrySentimentOut]
    recent_items: list[ConsensusItemOut]
