from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from datetime import datetime
from starlette.requests import Request
from authlib.integrations.starlette_client import OAuthError

from utils.email_utlis import send_verification_email
from utils.auth_google_utils import oauth_google_authorize_redirect, oauth_google_authorize_access_token
from services.jwt_service import (
    get_token_service,
    JWTService,
    TokenPair,
    bearer_scheme,
)
from services.user import get_user_service, UserService
from fastapi.security import HTTPAuthorizationCredentials
from models.token_models import TokenType
from models.user import User
from pydantic import BaseModel, EmailStr
from typing import Optional
from starlette.responses import RedirectResponse
import os

FRONTEND_URL = os.getenv("FRONTEND_URL")

auth_router = APIRouter(prefix="/auth", tags=["auth"])

# ==================== EMAIL AUTHENTICATION ====================

class EmailLoginRequest(BaseModel):
    email: EmailStr

@auth_router.post("/login")
async def login_via_email(
    payload: EmailLoginRequest,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(get_user_service),
    token_service: JWTService = Depends(get_token_service),
):
    email = payload.email
    user = user_service.get_user_by_email(email)
    if not user:
        user = User(email=email)
        user = user_service.create_user(user)

    token = token_service.create_email_verification_token(data={"sub": user.email})
    background_tasks.add_task(send_verification_email, email, token)

    return {"message": "Verification code sent", "email": email}


@auth_router.get("/email/verify-token/")
async def verify_email_token(token: str, token_service: JWTService = Depends(get_token_service)):
    payload = token_service.validate_email_verified_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")
    data = {"sub": email}
    access_token, expires_in = token_service.create_access_token(data=data)
    refresh_token = token_service.create_refresh_token(data=data)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, token_type="bearer", expires_in=expires_in)


@auth_router.post("/refresh-token")
async def refresh_tokens(
    refresh_token: str,
    user_service: UserService = Depends(get_user_service),
    token_service: JWTService = Depends(get_token_service),
):

    payload = token_service.validate_refresh_token(refresh_token)
    email = payload.get("sub")
    old_jti = payload["jti"]
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    # Rotate refresh token: blacklist the old refresh jti
    token_service.blacklist_token(
        jti=old_jti,
        token_type=TokenType.REFRESH,
        user_id=user.id,
        expires_at=datetime.fromtimestamp(payload["exp"]),
        reason="rotated",
    )

    access_token, expires_in = token_service.create_access_token(data={"sub": user.email})
    new_refresh_token = token_service.create_refresh_token(data={"sub": user.email})

    return TokenPair(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer", expires_in=expires_in)


@auth_router.post("/logout")
async def logout(
    refresh_token: str | None = None,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    token_service: JWTService = Depends(get_token_service),
    user_service: UserService = Depends(get_user_service),
):
    access_token = credentials.credentials
    try:
        token_data = token_service.validate_access_token(access_token)
        email = token_data.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    if refresh_token:
        payload_r = token_service.validate_refresh_token(refresh_token)
        r_jti = payload_r.get("jti")
        r_exp = payload_r.get("exp")
        if r_jti:
            token_service.blacklist_token(
                jti=r_jti,
                token_type=TokenType.REFRESH,
                user_id=user.id,
                expires_at=datetime.fromtimestamp(r_exp),
                reason="logout",
            )

    return {"message": "Logged out"}

# ==================== GOOGLE AUTHENTICATION ====================

@auth_router.get("/google/login")
async def login_via_google(request: Request):
    redirect_uri = request.url_for('callback_via_google')
    return await oauth_google_authorize_redirect(request, redirect_uri)

@auth_router.get("/google/callback")
async def callback_via_google(
    request: Request, 
    user_service: UserService = Depends(get_user_service), 
    token_service: JWTService = Depends(get_token_service)
):
    """
    Callback function for Google OAuth
    :param request: Request object
    :param user_service: User service

    Validate the request, get the google acces token (only validate login, we are not storing the google access token)
    create a new app access token

    :return: Token
    """
    try:
        token = await oauth_google_authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    if not token:
        raise HTTPException(status_code=400, detail="No token returned from Google")
    
    # access_token, refresh_token = user_service.process_google_login(token['userinfo'])
    # return TokenPair(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    token = token_service.create_google_verification_token(data={"sub": token['userinfo']['email']})
    # return token
    return RedirectResponse(f"{FRONTEND_URL}/login/google-validate?token={token}")


@auth_router.get("/google/verify-token/")
async def verify_google_token(token: str, token_service: JWTService = Depends(get_token_service)):
    payload = token_service.validate_google_verified_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")
    data = {"sub": email}
    access_token, expires_in = token_service.create_access_token(data=data)
    refresh_token = token_service.create_refresh_token(data=data)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, token_type="bearer", expires_in=expires_in)

