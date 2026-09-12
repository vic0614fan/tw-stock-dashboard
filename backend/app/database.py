from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./tw_stock.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_columns():
    """輕量級的『補欄位』機制：專案還沒上 Alembic 這類正式 migration 工具，
    Base.metadata.create_all() 只會建新表，不會幫既有的表補新欄位，所以每次
    model 加了新欄位，要在這裡手動補一行，啟動時會自動幫舊資料庫 ALTER TABLE。
    """
    inspector = inspect(engine)
    if "stocks" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("stocks")}
        if "industry" not in existing:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE stocks ADD COLUMN industry VARCHAR"))
                conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
