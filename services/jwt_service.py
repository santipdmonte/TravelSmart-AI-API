from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import os
import uuid
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.token_models import TokenBlocklist, TokenType


load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
GOOGLE_TOKEN_EXPIRE_MINUTES = int(os.getenv("GOOGLE_TOKEN_EXPIRE_MINUTES", "1"))
EMAIL_TOKEN_EXPIRE_MINUTES = int(os.getenv("EMAIL_TOKEN_EXPIRE_MINUTES", "5"))
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


bearer_scheme = HTTPBearer(
    scheme_name="Bearer Token",
    description="Enter your access token here",
)


class JWTService:
    def __init__(self, db: Depends(get_db)):
        self.db = db
        self.sercret = SECRET_KEY
        self.algorithm = ALGORITHM

    # ==================== DB-RELATED METHODS ====================
    def is_blacklisted(self, jti: str) -> bool:
        return (
            self.db.query(TokenBlocklist)
            .filter(TokenBlocklist.jti == jti)
            .first()
            is not None
        )

    def blacklist_token(
        self,
        *,
        jti: str,
        token_type: TokenType,
        user_id: Optional[UUID],
        expires_at: datetime,
        reason: Optional[str] = None,
    ) -> TokenBlocklist:
        if self.is_blacklisted(jti):
            return (
                self.db.query(TokenBlocklist)
                .filter(TokenBlocklist.jti == jti)
                .first()
            )

        entry = TokenBlocklist(
            jti=jti,
            token_type=token_type.value if hasattr(token_type, "value") else str(token_type),
            user_id=user_id,
            expires_at=expires_at,
            reason=reason,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    # ==================== JWT HELPERS ====================
    @staticmethod
    def _with_standard_claims(data: dict, *, token_type: str, exp_delta: timedelta) -> dict:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + exp_delta
        jti = uuid.uuid4().hex
        to_encode.update({"exp": expire, "type": token_type, "jti": jti})
        expires_in = exp_delta.total_seconds()
        return to_encode, expires_in


    # ==================== TOKEN CREATION ====================

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode, expires_in = self._with_standard_claims(data, token_type="access", exp_delta=expires_delta)
        return jwt.encode(to_encode, self.sercret, algorithm=self.algorithm), expires_in


    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode, _ = self._with_standard_claims(data, token_type="refresh", exp_delta=expires_delta)
        return jwt.encode(to_encode, self.sercret, algorithm=self.algorithm)


    def create_email_verification_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=EMAIL_TOKEN_EXPIRE_MINUTES)
        to_encode, _ = self._with_standard_claims(data, token_type="email_verified", exp_delta=expires_delta)
        return jwt.encode(to_encode, self.sercret, algorithm=self.algorithm)


    def create_google_verification_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=GOOGLE_TOKEN_EXPIRE_MINUTES)
        to_encode, _ = self._with_standard_claims(data, token_type="google_verified", exp_delta=expires_delta)
        return jwt.encode(to_encode, self.sercret, algorithm=self.algorithm)


    # ==================== TOKEN VALIDATION ====================

    def validate_access_token(self, token_str: str) -> dict:
        try:
            payload = jwt.decode(token_str, self.sercret, algorithms=[self.algorithm])
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type: {payload.get('token_type')}",
                )
            return payload
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    def validate_email_verified_token(self, token_str: str) -> dict:
        try:
            payload = jwt.decode(token_str, self.sercret, algorithms=[self.algorithm])
            if payload.get("type") != "email_verified":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type: {payload.get('token_type')}",
                )
            return payload
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    def validate_google_verified_token(self, token_str: str) -> dict:
        try:
            payload = jwt.decode(token_str, self.sercret, algorithms=[self.algorithm])
            if payload.get("type") != "google_verified":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type: {payload.get('token_type')}",
                )
            return payload
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    def validate_refresh_token(self, refresh_token: str) -> dict:
        try:
            payload = jwt.decode(refresh_token, self.sercret, algorithms=[self.algorithm])
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type: {payload.get('token_type')}",
                )
            jti = payload.get("jti")
            if jti and self.is_blacklisted(jti):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
            return payload
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


def get_token_service(db: Session = Depends(get_db)) -> JWTService:
    return JWTService(db)


# ==================== DEPENDENCY HELPERS ====================
def get_access_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    token_service: JWTService = Depends(get_token_service),
):
    return token_service.validate_access_token(credentials.credentials)


def get_refresh_payload(
    refresh_token: str,
    token_service: JWTService = Depends(get_token_service),
):
    return token_service.validate_refresh_token(refresh_token)


def get_email_verification_payload(
    token: str,
    token_service: JWTService = Depends(get_token_service),
):
    return token_service.validate_email_verified_token(token)

