# ==========================================
# SCRIPT: Database Initialization
# PURPOSE: Initialize database and create all tables
# ==========================================

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, engine
from app import models


def init_db():
    """
    Initialize database by creating all tables.
    Safe to run multiple times - existing tables are skipped.
    """
    print("\n" + "="*60)
    print("🗄️  DATABASE INITIALIZATION")
    print("="*60)
    
    print("\n📊 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
    
    print("\n📋 Created tables:")
    print("  ✓ users")
    print("  ✓ user_points_history")
    print("  ✓ buttons")
    print("  ✓ media_files")
    print("  ✓ channels")
    print("  ✓ user_channel_membership")
    print("  ✓ support_tickets")
    print("  ✓ broadcast_campaigns")
    print("  ✓ broadcast_receipts")
    print("  ✓ scheduled_tasks")
    print("  ✓ admin_users")
    print("  ✓ admin_activity_logs")
    
    print("\n" + "="*60)
    print("✅ Database initialization completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    init_db()
