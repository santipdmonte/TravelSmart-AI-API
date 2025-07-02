from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models.user import User
from services.user import UserService, get_user_service
import os
from dotenv import load_dotenv
import uuid
import time

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Security scheme
security = HTTPBearer()


def create_access_token(user_id: uuid.UUID, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    now = time.time()
    if expires_delta:
        expire = now + expires_delta.total_seconds()
    else:
        expire = now + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    to_encode = {
        "sub": str(user_id),
        "exp": int(expire),
        "type": "access",
        "iat": int(now)
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create JWT refresh token"""
    now = time.time()
    expire = now + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
    
    to_encode = {
        "sub": str(user_id),
        "exp": int(expire),
        "type": "refresh",
        "iat": int(now)
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or time.time() > exp:
            return None
        
        return payload
    
    except JWTError:
        return None


def decode_token(token: str) -> Optional[uuid.UUID]:
    """Decode token and return user ID"""
    payload = verify_token(token)
    if payload is None:
        return None
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None
    
    try:
        return uuid.UUID(user_id_str)
    except ValueError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify token and get user ID
        user_id = decode_token(token)
        if user_id is None:
            raise credentials_exception
        
        # Get user from database
        user = user_service.get_user_by_id(user_id)
        if user is None:
            raise credentials_exception
        
        # Check if user is active
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )
        
        return user
    
    except JWTError:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (additional validation)"""
    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted"
        )
    
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    user_service: UserService = Depends(get_user_service)
) -> Optional[User]:
    """Get current authenticated user from JWT token, returns None if not authenticated"""
    if not credentials:
        return None
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify token and get user ID
        user_id = decode_token(token)
        if user_id is None:
            return None
        
        # Get user from database
        user = user_service.get_user_by_id(user_id)
        if user is None:
            return None
        
        # Check if user is active
        if user.status != "active":
            return None
        
        return user
    
    except JWTError:
        return None


def require_roles(*allowed_roles: str):
    """Decorator factory for role-based access control"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker


# Convenience dependencies for common roles
get_admin_user = require_roles("admin")
get_premium_user = require_roles("premium", "admin")
get_moderator_user = require_roles("moderator", "admin")


def create_token_response(user: User) -> Dict[str, Any]:
    """Create standardized token response"""
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        "user_id": str(user.id)
    } 