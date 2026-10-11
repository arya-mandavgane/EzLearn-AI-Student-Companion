"""
Database setup and SQLAlchemy Base stub for Phase 1.
"""

from typing import Generator
from app.core.config import settings

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker

    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    engine = create_engine(settings.database_url, connect_args=connect_args)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    def get_db() -> Generator:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def init_db():
        from app.models import models  # import all models
        Base.metadata.create_all(bind=engine)

except ImportError:
    # Fallback stub for Phase 0 before SQLAlchemy is added in Phase 1
    engine = None
    SessionLocal = None

    class Base:  # type: ignore
        pass

    def get_db() -> Generator:
        yield None
