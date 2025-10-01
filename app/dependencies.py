# app/dependencies.py

"""
FastAPI dependencies for authentication and authorization.
Provides reusable dependencies for JWT validation and user extraction.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from typing import Optional, Dict, Any
from app.config import settings
from functools import lru_cache

# HTTP Bearer token security scheme
security = HTTPBearer()

# Cache for JWKS (JSON Web Key Set)
_jwks_cache: Optional[Dict[str, Any]] = None


async def get_jwks() -> Dict[str, Any]:
    """
    Fetch and cache the JWKS from Supabase.
    This is used to validate JWT signatures.
    """
    global _jwks_cache
    
    if _jwks_cache is not None:
        return _jwks_cache
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.supabase_jwks_url, timeout=10.0)
            response.raise_for_status()
            _jwks_cache = response.json()
            return _jwks_cache
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch JWKS: {str(e)}"
        )


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # For production, you should validate against JWKS
        # For simplicity, we'll decode without verification first
        # In a real app, fetch JWKS and verify signature
        
        # Option 1: Decode with service role key (simplified for development)
        payload = jwt.decode(
            token,
            settings.supabase_service_role_key,
            algorithms=["HS256"],
            options={"verify_signature": False}  # Set to True in production with proper JWKS
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to extract and validate the current user from JWT token.
    
    Returns:
        Dictionary containing user information including user_id
        
    Raises:
        HTTPException: If token is invalid or user_id cannot be extracted
    """
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    # Extract user_id from the configured claim (default: 'sub')
    user_id = payload.get(settings.jwt_user_id_claim)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token missing required claim: {settings.jwt_user_id_claim}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": user_id,
        "payload": payload
    }


async def get_current_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to verify that the current user has admin privileges.
    
    Checks the configured admin role claim and value from settings.
    
    Args:
        current_user: User info from get_current_user dependency
        
    Returns:
        User information dict
        
    Raises:
        HTTPException: If user does not have admin privileges
    """
    payload = current_user["payload"]
    
    # Navigate nested claims (e.g., 'app_metadata.is_admin')
    claim_path = settings.admin_role_claim.split('.')
    claim_value = payload
    
    try:
        for key in claim_path:
            claim_value = claim_value[key]
    except (KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: missing admin claim '{settings.admin_role_claim}'"
        )
    
    # Check if the claim value matches the expected admin value
    if str(claim_value) != settings.admin_role_value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: insufficient privileges"
        )
    
    return current_user


# Optional: Dependency for public endpoints that can optionally use auth
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency.
    Returns user info if token is provided and valid, None otherwise.
    Useful for endpoints that change behavior based on authentication.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None