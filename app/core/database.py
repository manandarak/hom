from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, declarative_base
from src.app.core.config import settings

# This approach handles special characters in passwords automatically
# If settings.DATABASE_URL is "mysql+pymysql://root:Manan35635@127.0.0.1:3306/hom_db"
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()