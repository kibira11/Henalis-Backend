# app/dependencies.py

"""
Dependencies for authentication and authorization.
Simplified for Neon (no Supabase).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings
from typing import Dict, Any

security = HTTPBearer()


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode JWT using local secret key.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,           # secret stored in .env
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Validate JWT and return current user info.
    """
    token = credentials.credentials
    payload = decode_jwt_token(token)

    user_id = payload.get(settings.jwt_user_id_claim)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing claim: {settings.jwt_user_id_claim}"
        )

    return {
        "user_id": user_id,
        "payload": payload
    }


async def get_current_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Restrict access to admins only.
    """
    if payload := current_user.get("payload"):
        if payload.get("role") == "admin":
            return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required"
    )
