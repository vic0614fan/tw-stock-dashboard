from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine
from app.models import Influencer
from app.routers import chip_data, influencers, institutional_flow, news, opinions

Base.metadata.create_all(bind=engine)


def _seed_influencers():
    db = SessionLocal()
    try:
        if not db.query(Influencer).filter(Influencer.handle == "x.stock_men").first():
            db.add(
                Influencer(
                    name="Chris",
                    platform="threads",
                    handle="x.stock_men",
                    profile_url="https://www.threads.net/@x.stock_men",
                    category="產業分析／技術分析",
                )
            )
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


@app.get("/")
def root():
    return {"status": "ok"}
