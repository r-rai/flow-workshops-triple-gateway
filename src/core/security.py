import time
from typing import Dict, Any, List, Optional
from fastapi import Header, HTTPException, Depends, status
from jose import jwt, JWTError
from src.core.config import settings

class Principal:
    def __init__(self, id: str, role: str, scopes: List[str], delegated_by: Optional[str] = None, auth_method: str = "bearer"):
        self.id = id
        self.role = role
        self.scopes = scopes
        self.delegated_by = delegated_by
        self.auth_method = auth_method

def get_current_principal(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Principal:
    """
    Extracts authoritative identity ONLY from validated credentials.
    Strips and ignores any caller-provided X-User-Id, X-Role, etc.
    """
    # 1. Check Bearer Token (JWT from Gate 3 / Keycloak / Lab Issuer)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
        try:
            claims = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.API_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )
            scopes = claims.get("scope", "").split()
            role = claims.get("role", "viewer")
            sub = claims.get("sub", "anonymous")
            delegated_by = claims.get("act", {}).get("sub")
            return Principal(id=sub, role=role, scopes=scopes, delegated_by=delegated_by, auth_method="bearer")
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired bearer token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 2. Check X-API-Key (Workshop Gate 3 static lab key for W1 operator)
    if x_api_key:
        if x_api_key == settings.API_KEY_SECRET:
            return Principal(
                id="w1-lab-operator",
                role="operator",
                scopes=["api:accounts:read", "api:payments:write", "api:cases:read", "api:incidents:write"],
                auth_method="api_key",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Missing credentials
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing Gate 3 authentication credential",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_scope(scope_name: str):
    def _checker(principal: Principal = Depends(get_current_principal)):
        if scope_name not in principal.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient scope. Required: '{scope_name}', present: {principal.scopes}",
            )
        return principal
    return _checker

def create_jwt_token(
    subject: str,
    audience: str,
    scopes: List[str],
    role: str = "service",
    expires_in_seconds: int = 3600,
    delegated_by: Optional[str] = None
) -> str:
    now = int(time.time())
    claims = {
        "iss": settings.JWT_ISSUER,
        "sub": subject,
        "aud": audience,
        "role": role,
        "scope": " ".join(scopes),
        "iat": now,
        "exp": now + expires_in_seconds
    }
    if delegated_by:
        claims["act"] = {"sub": delegated_by}
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

