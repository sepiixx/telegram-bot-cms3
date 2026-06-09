# ==========================================
# MODULE: MAIN APPLICATION
# PURPOSE: FastAPI application entry point
# ==========================================

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import timedelta
import logging
from pathlib import Path

from app.config import get_settings
from app.database import get_db, engine, Base
from app.middleware import get_cors_config, get_current_admin, check_rate_limit
from app.security import create_access_token, hash_password, verify_password
from app import schemas, models
from app.repositories import AdminUserRepository

# ========== Settings ==========
settings = get_settings()

# ========== Logging Configuration ==========
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== Create Database Tables ==========
Base.metadata.create_all(bind=engine)
logger.info("✅ Database tables initialized")


# ==========================================
# CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Dynamic Telegram Bot CMS with Web Admin Panel"
)


# ========== Add CORS Middleware ==========
cors_config = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)

logger.info("✅ CORS middleware configured")


# ========== Mount Static Files ==========
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ==========================================
# HEALTH CHECK ENDPOINTS
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - welcome page"""
    return """
    <html>
        <head>
            <title>Telegram Bot CMS</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 50px; }
                h1 { color: #0088cc; }
                a { color: #0088cc; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>🤖 Telegram Bot CMS</h1>
            <p>Dynamic Bot Management System</p>
            <h2>Quick Links:</h2>
            <ul>
                <li><a href="/docs">API Documentation (Swagger UI)</a></li>
                <li><a href="/redoc">API Documentation (ReDoc)</a></li>
                <li><a href="/admin">Admin Panel</a></li>
            </ul>
            <hr>
            <p><strong>Version:</strong> {}</p>
            <p><strong>Status:</strong> ✅ Running</p>
        </body>
    </html>
    """.format(settings.APP_VERSION)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "app_name": settings.APP_NAME
    }


# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/api/auth/login", response_model=schemas.LoginResponse, tags=["Authentication"])
async def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint for admin users.
    
    Returns JWT token for authenticated admin.
    """
    admin_repo = AdminUserRepository(db)
    admin = admin_repo.get_by_username(credentials.username)
    
    if not admin or not verify_password(credentials.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": admin.username, "user_id": admin.id},
        expires_delta=timedelta(days=settings.JWT_EXPIRE_DAYS)
    )
    
    # Update last login
    admin_repo.update(admin.id, {"last_login": __import__('datetime').datetime.utcnow()})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": schemas.AdminUserResponse.from_orm(admin)
    }


@app.post("/api/auth/logout", tags=["Authentication"])
async def logout(current_admin: dict = Depends(get_current_admin)):
    """
    Logout endpoint (token invalidation on client side).
    """
    return {"message": "Successfully logged out"}


# ==========================================
# ADMIN USER ENDPOINTS
# ==========================================

@app.post("/api/admin/users", response_model=schemas.AdminUserResponse, tags=["Admin Users"])
async def create_admin_user(
    user_data: schemas.AdminUserCreate,
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create new admin user (admin only).
    """
    admin_repo = AdminUserRepository(db)
    
    # Check if user already exists
    if admin_repo.get_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new admin
    hashed_password = hash_password(user_data.password)
    admin_data = {
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hashed_password,
        "is_superuser": user_data.is_superuser
    }
    
    new_admin = admin_repo.create(admin_data)
    return schemas.AdminUserResponse.from_orm(new_admin)


@app.get("/api/admin/users", response_model=list[schemas.AdminUserResponse], tags=["Admin Users"])
async def list_admin_users(
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List all admin users.
    """
    admin_repo = AdminUserRepository(db)
    admins = admin_repo.get_all()
    return [schemas.AdminUserResponse.from_orm(admin) for admin in admins]


# ==========================================
# DASHBOARD ENDPOINTS
# ==========================================

@app.get("/api/dashboard/stats", response_model=schemas.DashboardStats, tags=["Dashboard"])
async def get_dashboard_stats(
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics.
    """
    from app.repositories import (
        UserRepository, ButtonRepository, SupportTicketRepository,
        BroadcastRepository
    )
    
    user_repo = UserRepository(db)
    button_repo = ButtonRepository(db)
    ticket_repo = SupportTicketRepository(db)
    broadcast_repo = BroadcastRepository(db)
    
    total_users = user_repo.count()
    active_users = user_repo.count_active_users()
    total_buttons = button_repo.count()
    open_tickets = len(ticket_repo.get_open_tickets())
    
    # Referral stats
    users = user_repo.get_all(limit=10000)
    total_referrals = sum(u.referral_count for u in users)
    
    # Broadcast stats
    campaigns = broadcast_repo.get_all(limit=10000)
    broadcast_stats = {
        "total_campaigns": len(campaigns),
        "total_sent": sum(c.sent_count for c in campaigns),
        "avg_success_rate": sum(c.success_rate for c in campaigns) / len(campaigns) if campaigns else 0
    }
    
    return schemas.DashboardStats(
        total_users=total_users,
        active_users=active_users,
        total_buttons=total_buttons,
        support_tickets_open=open_tickets,
        total_referrals=total_referrals,
        broadcast_stats=broadcast_stats
    )


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP Exception: {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled Exception: {str(exc)}")
    return {
        "error": "Internal server error",
        "status_code": 500
    }


# ==========================================
# STARTUP AND SHUTDOWN EVENTS
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info(f"🚀 Starting {settings.APP_NAME}")
    logger.info(f"📊 Database: {settings.DATABASE_URL}")
    logger.info(f"🤖 Bot Token: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
    logger.info("✅ Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down application")


# ==========================================
# EXPORT APP
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.FAST_API_HOST,
        port=settings.FAST_API_PORT,
        reload=settings.FAST_API_RELOAD
    )
