"""Authentication utility functions for password hashing and JWT tokens."""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from passlib.context import CryptContext

from src.auth.config import auth_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None,
) -> str:
    """Create a JWT access token.
    
    Args:
        data: Dictionary containing token claims (must include 'sub' for user_id and 'role_id')
        expires_delta: Optional expiration time delta (defaults to ACCESS_TOKEN_EXPIRE_MINUTES)
        jti: Optional JWT ID for token revocation
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    })
    
    # Add JWT ID if provided
    if jti:
        to_encode["jti"] = jti
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        auth_settings.SECRET_KEY,
        algorithm=auth_settings.ALGORITHM,
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload dictionary, or None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            auth_settings.SECRET_KEY,
            algorithms=[auth_settings.ALGORITHM],
        )
        return payload
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None


def generate_invitation_token() -> str:
    """Generate a secure invitation token.
    
    Returns:
        Random token string
    """
    return secrets.token_urlsafe(32)


def generate_password_reset_token() -> str:
    """Generate a secure password reset token.
    
    Returns:
        Random token string
    """
    return secrets.token_urlsafe(32)
