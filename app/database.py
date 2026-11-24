
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured in .env")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "ssl": {}
    }
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
