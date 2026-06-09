# ==========================================
# MODULE: MIDDLEWARE
# PURPOSE: HTTP middleware for authentication and CORS
# ==========================================

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from typing import Optional
from app.security import decode_token
from app.config import get_settings

# ========== Security Scheme ==========
security = HTTPBearer()


# ==========================================
# AUTHENTICATION MIDDLEWARE
# PURPOSE: Verify JWT tokens
# ==========================================

async def get_current_admin(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """
    Dependency to verify JWT token and get current admin user.
    
    Args:
        credentials: HTTP Bearer token
    
    Returns:
        Token data if valid
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"username": token_data.username, "user_id": token_data.user_id}


async def get_optional_admin(request: Request) -> Optional[dict]:
    """
    Optional admin authentication.
    Returns None if no token provided or token is invalid.
    
    Args:
        request: HTTP request
    
    Returns:
        Token data if valid, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        return None
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None
        
        token_data = decode_token(token)
        if token_data is None:
            return None
        
        return {"username": token_data.username, "user_id": token_data.user_id}
    
    except (ValueError, IndexError):
        return None


# ==========================================
# RATE LIMITING
# PURPOSE: Prevent abuse
# ==========================================

class RateLimiter:
    """Simple rate limiter using in-memory storage"""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {key: [(timestamp, count)]}
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            key: Unique key (IP, user ID, etc.)
        
        Returns:
            True if allowed, False if rate limited
        """
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside window
        self.requests[key] = [
            ts for ts in self.requests[key] if ts > window_start
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Add new request
        self.requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=get_settings().RATE_LIMIT_PER_MINUTE,
    window_seconds=60
)


async def check_rate_limit(request: Request) -> bool:
    """
    Check if request is within rate limit.
    
    Args:
        request: HTTP request
    
    Returns:
        True if allowed
    
    Raises:
        HTTPException: If rate limited
    """
    # Use client IP as key
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later."
        )
    
    return True


# ==========================================
# INPUT VALIDATION MIDDLEWARE
# PURPOSE: Validate and sanitize inputs
# ==========================================

async def validate_json_body(request: Request) -> dict:
    """
    Validate and extract JSON body.
    
    Args:
        request: HTTP request
    
    Returns:
        Parsed JSON body
    
    Raises:
        HTTPException: If JSON is invalid
    """
    try:
        body = await request.json()
        return body
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )


# ==========================================
# CORS CONFIGURATION
# PURPOSE: Configure Cross-Origin Resource Sharing
# ==========================================

def get_cors_config() -> dict:
    """
    Get CORS configuration.
    
    Returns:
        CORS configuration dictionary
    """
    settings = get_settings()
    
    return {
        "allow_origins": settings.CORS_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["*"],
        "expose_headers": ["Content-Length", "Content-Range"],
        "max_age": 600,
    }
