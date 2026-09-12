"""每日／每週自動抓取排程。跟 FastAPI 在同一個行程裡跑，所以後端伺服器需要保持開著
（例如整天開著 `uvicorn app.main:app`），排程才會實際觸發。
"""

import logging
from datetime import date
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.ingest import ingest_chip_data, ingest_influencer_opinions, ingest_institutional_flow, ingest_news, ingest_shareholding
from app.models import Influencer
from app.services.llm_classifier import LLMNotConfiguredError
from app.services.twse import NoTradingDataError

logger = logging.getLogger("scheduler")
TAIPEI = ZoneInfo("Asia/Taipei")


def job_fetch_twse_daily():
    """交易日盤後執行：資金流向 + 籌碼面。非交易日（假日）會直接跳過，不算錯誤。"""
    today = date.today()
    db = SessionLocal()
    try:
        try:
            n = ingest_institutional_flow(db, today)
            logger.info("排程：資金流向 %s 抓到 %d 筆", today, n)
        except NoTradingDataError:
            logger.info("排程：%s 非交易日，跳過資金流向", today)
        except Exception:
            logger.exception("排程：資金流向抓取失敗")

        try:
            n = ingest_chip_data(db, today)
            logger.info("排程：籌碼面 %s 抓到 %d 筆", today, n)
        except NoTradingDataError:
            logger.info("排程：%s 非交易日，跳過籌碼面", today)
        except Exception:
            logger.exception("排程：籌碼面抓取失敗")
    finally:
        db.close()


def job_fetch_opinions_and_news_daily():
    """每天抓意見領袖新貼文 + 財經新聞。未設定 ANTHROPIC_API_KEY 時整批跳過並記警告。"""
    db = SessionLocal()
    try:
        for influencer in db.query(Influencer).all():
            try:
                result = ingest_influencer_opinions(db, influencer)
                logger.info("排程：%s 新增 %d 則意見", influencer.name, result["opinions_saved"])
            except LLMNotConfiguredError:
                logger.warning("排程：未設定 ANTHROPIC_API_KEY，跳過意見領袖抓取")
                break
            except Exception:
                logger.exception("排程：抓 %s 的貼文失敗", influencer.name)

        try:
            result = ingest_news(db)
            logger.info("排程：新聞新增 %d 則", result["items_saved"])
        except LLMNotConfiguredError:
            logger.warning("排程：未設定 ANTHROPIC_API_KEY，跳過新聞抓取")
        except Exception:
            logger.exception("排程：新聞抓取失敗")
    finally:
        db.close()


def job_fetch_shareholding_weekly():
    """TDCC 集保戶股權分散表每週更新一次，週六早上抓通常已經有最新一週的資料。"""
    db = SessionLocal()
    try:
        trade_date, n = ingest_shareholding(db)
        if trade_date is None:
            logger.info("排程：大戶持股比例沒有新資料可抓（可能還沒有任何股票主檔）")
        else:
            logger.info("排程：大戶持股比例 %s 抓到 %d 筆", trade_date, n)
    except Exception:
        logger.exception("排程：大戶持股比例抓取失敗")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=TAIPEI)
    # 盤後資料約下午 3 點後公布，抓晚一點比較保險
    scheduler.add_job(job_fetch_twse_daily, CronTrigger(day_of_week="mon-fri", hour=15, minute=30))
    scheduler.add_job(job_fetch_opinions_and_news_daily, CronTrigger(day_of_week="mon-fri", hour=16, minute=0))
    scheduler.add_job(job_fetch_shareholding_weekly, CronTrigger(day_of_week="sat", hour=9, minute=0))
    scheduler.start()
    logger.info("排程器已啟動")
    return scheduler
