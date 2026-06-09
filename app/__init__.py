# ==========================================
# MODULE: PACKAGE INITIALIZATION
# PURPOSE: Application package entry point
# ==========================================

__version__ = "1.0.0"
__author__ = "Telegram Bot CMS"

from app.database import Base, engine, SessionLocal, get_db
from app.config import get_settings

__all__ = ["Base", "engine", "SessionLocal", "get_db", "get_settings"]
