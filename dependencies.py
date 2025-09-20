from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from services.jwt_service import bearer_scheme, get_token_service, JWTService
from services.user import UserService, get_user_service
from models.user import User, UserRoleEnum
from typing import Annotated
from fastapi import status
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from models.user import UserStatusEnum

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user_service: UserService = Depends(get_user_service)
):
    token = credentials.credentials
    token_service: JWTService = get_token_service()
    token_data = token_service.validate_access_token(token)
    email = token_data.get("sub")
    
    user = user_service.get_user_by_email(email=email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.status != UserStatusEnum.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role != UserRoleEnum.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin user required")
    return current_user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    token_service: JWTService = Depends(get_token_service),
    user_service: UserService = Depends(get_user_service)
):
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        token_data = token_service.validate_access_token(token)
        email = token_data.get("sub")
        if not email:
            return None
        return user_service.get_user_by_email(email=email)
    except (InvalidTokenError, ExpiredSignatureError):
        return None