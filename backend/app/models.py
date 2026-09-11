from sqlalchemy import Column, String, Integer, BigInteger, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    stock_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)

    institutional_flows = relationship("InstitutionalFlow", back_populates="stock")
    chip_data = relationship("ChipData", back_populates="stock")


class InstitutionalFlow(Base):
    __tablename__ = "institutional_flow"
    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_institutional_flow_stock_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String, ForeignKey("stocks.stock_id"), nullable=False)
    date = Column(Date, nullable=False)

    foreign_net = Column(BigInteger, nullable=False)  # 外資合計買賣超股數
    trust_net = Column(BigInteger, nullable=False)  # 投信買賣超股數
    dealer_net = Column(BigInteger, nullable=False)  # 自營商買賣超股數(合計)
    total_net = Column(BigInteger, nullable=False)  # 三大法人買賣超股數

    stock = relationship("Stock", back_populates="institutional_flows")


class ChipData(Base):
    __tablename__ = "chip_data"
    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_chip_data_stock_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String, ForeignKey("stocks.stock_id"), nullable=False)
    date = Column(Date, nullable=False)

    margin_buy_balance = Column(BigInteger, nullable=False)  # 融資今日餘額（張）
    margin_sell_balance = Column(BigInteger, nullable=False)  # 融券今日餘額（張）

    stock = relationship("Stock", back_populates="chip_data")


class Influencer(Base):
    __tablename__ = "influencers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)  # 顯示名稱，例如「Chris」
    platform = Column(String, nullable=False)  # threads / youtube / ptt ...
    handle = Column(String, nullable=False)  # 平台帳號，例如「x.stock_men」
    profile_url = Column(String, nullable=False)
    category = Column(String, nullable=True)  # 技術分析／產業分析／總經／基本面

    opinions = relationship("OpinionData", back_populates="influencer")


class OpinionData(Base):
    __tablename__ = "opinion_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    influencer_id = Column(Integer, ForeignKey("influencers.id"), nullable=False)

    source_url = Column(String, unique=True, nullable=False)
    published_at = Column(DateTime, nullable=True)  # 原文發布時間（能解析到才存）
    scraped_at = Column(DateTime, nullable=False, server_default=func.now())

    raw_content = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)  # 多 / 空 / 中性
    summary = Column(String, nullable=False)

    influencer = relationship("Influencer", back_populates="opinions")
    stocks = relationship("OpinionStock", back_populates="opinion")


class OpinionStock(Base):
    __tablename__ = "opinion_stocks"
    __table_args__ = (UniqueConstraint("opinion_id", "stock_id", name="uq_opinion_stock"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    opinion_id = Column(Integer, ForeignKey("opinion_data.id"), nullable=False)
    stock_id = Column(String, nullable=False)  # 不設 FK 到 stocks，避免文章提到還沒抓過盤後資料的股票時寫入失敗

    opinion = relationship("OpinionData", back_populates="stocks")
