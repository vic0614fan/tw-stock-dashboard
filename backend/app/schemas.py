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
