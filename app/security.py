# ==========================================
# MODULE: AUTHENTICATION AND SECURITY
# PURPOSE: JWT token generation and password hashing
# ==========================================

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import get_settings
from app import schemas

# ========== Password Hashing Context ==========
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==========================================
# PASSWORD UTILITIES
# PURPOSE: Hash and verify passwords
# ==========================================

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==========================================
# JWT TOKEN UTILITIES
# PURPOSE: Generate and validate JWT tokens
# ==========================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token
    """
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[schemas.TokenData]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token to decode
    
    Returns:
        TokenData if valid, None if invalid
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None:
            return None
        
        return schemas.TokenData(username=username, user_id=user_id)
    
    except JWTError:
        return None


# ==========================================
# VALIDATION UTILITIES
# PURPOSE: Validate common inputs
# ==========================================

def validate_password(password: str) -> bool:
    """
    Validate password meets requirements.
    
    Args:
        password: Password to validate
    
    Returns:
        True if password is valid
    """
    settings = get_settings()
    
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False
    
    # Add more validation rules as needed
    return True


def validate_telegram_id(telegram_id: int) -> bool:
    """
    Validate Telegram user ID.
    
    Args:
        telegram_id: Telegram ID to validate
    
    Returns:
        True if valid format
    """
    return isinstance(telegram_id, int) and telegram_id > 0


def sanitize_input(input_str: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent injection.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not input_str:
        return ""
    
    # Truncate to max length
    sanitized = input_str[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", "&", "\"", "'", ";", "--", "/*", "*/"]
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    
    return sanitized.strip()
