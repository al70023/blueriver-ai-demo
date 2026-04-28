from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


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
