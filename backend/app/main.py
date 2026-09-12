from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine, ensure_columns
from app.models import Influencer
from app.routers import chip_data, consensus, influencers, institutional_flow, news, opinions, shareholding, stocks
from app.scheduler import start_scheduler

Base.metadata.create_all(bind=engine)
ensure_columns()


# handle 依平台意義不同：threads 是帳號、youtube 是 channel_id、blog 是 RSS 網址
_SEED_INFLUENCERS = [
    {
        "name": "Chris",
        "platform": "threads",
        "handle": "x.stock_men",
        "profile_url": "https://www.threads.net/@x.stock_men",
        "category": "產業分析／技術分析",
    },
    {
        "name": "Mr.Market市場先生",
        "platform": "blog",
        "handle": "https://rich01.com/feed/",
        "profile_url": "https://rich01.com/",
        "category": "理財教育／基本面",
    },
    {
        "name": "股乾爹 KuKanTieh",
        "platform": "youtube",
        "handle": "UCDDneQi63kJAdr3i5VCPzHg",
        "profile_url": "https://www.youtube.com/@kukantieh",
        "category": "總經數據分析",
    },
    {
        "name": "柴鼠兄弟 ZRBros",
        "platform": "youtube",
        "handle": "UC45i13dEfEVac2IEJT_Nr5Q",
        "profile_url": "https://www.youtube.com/@ZRBro",
        "category": "理財教育",
    },
    {
        "name": "郭哲榮分析師",
        "platform": "youtube",
        "handle": "UChfl3auNxAxOR3wy8a8ysQQ",
        "profile_url": "https://www.youtube.com/@s178",
        "category": "技術分析",
    },
    {
        "name": "老王愛說笑",
        "platform": "youtube",
        "handle": "UCvnLmiWt_zIVIh0zUm_j4Hw",
        "profile_url": "https://www.youtube.com/@oldwangstock",
        "category": "傳統技術分析",
    },
    {
        "name": "游庭皓的財經皓角",
        "platform": "youtube",
        "handle": "UC0lbAQVpenvfA2QqzsRtL_g",
        "profile_url": "https://www.youtube.com/channel/UC0lbAQVpenvfA2QqzsRtL_g",
        "category": "總經分析",
    },
]


def _seed_influencers():
    db = SessionLocal()
    try:
        for data in _SEED_INFLUENCERS:
            if not db.query(Influencer).filter(Influencer.handle == data["handle"]).first():
                db.add(Influencer(**data))
        db.commit()
    finally:
        db.close()


_seed_influencers()

app = FastAPI(title="台股盤後分析工具 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(institutional_flow.router)
app.include_router(chip_data.router)
app.include_router(influencers.router)
app.include_router(opinions.router)
app.include_router(news.router)
app.include_router(shareholding.router)
app.include_router(stocks.router)
app.include_router(consensus.router)

start_scheduler()


@app.get("/")
def root():
    return {"status": "ok"}
