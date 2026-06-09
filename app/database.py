# ==========================================
# MODULE: DATABASE CONNECTION AND SETUP
# PURPOSE: SQLAlchemy engine and session management
# ==========================================

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool
from typing import Generator
from app.config import get_settings

# ========== Database Configuration ==========
settings = get_settings()

# ========== Create SQLAlchemy Engine ==========
if "sqlite" in settings.DATABASE_URL:
    # SQLite configuration (development)
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DATABASE_ECHO,
    )
else:
    # PostgreSQL configuration (production)
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DATABASE_ECHO,
    )


# ========== SQLite Foreign Keys ==========
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Enable foreign keys for SQLite"""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ========== Session Factory ==========
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ========== Base Model Class ==========
Base = declarative_base()


# ========== Database Session Dependency ==========
def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to inject database sessions.
    Usage in route: async def route(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
