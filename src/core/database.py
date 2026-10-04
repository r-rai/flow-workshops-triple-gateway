import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    # If path is inside /app and /app does not exist, use ./data
    if "///app/" in db_url and not os.path.exists("/app"):
        db_url = "sqlite:///./data/flobank.sqlite"
    if "///" in db_url:
        path = db_url.split("///")[-1]
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(db_url, pool_pre_ping=True, pool_size=5, max_overflow=10)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
