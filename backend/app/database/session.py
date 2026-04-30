from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def get_database_url() -> str:
    if settings.database_url.startswith("postgresql://"):
        return settings.database_url.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )

    return settings.database_url


engine = create_engine(get_database_url())

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
