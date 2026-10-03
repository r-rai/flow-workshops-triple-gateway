import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Form, Request
from pydantic import BaseModel
from jose import jwt, JWTError
from src.core.config import settings

router = APIRouter(prefix="", tags=["OAuth2 & RFC 8693 Token Exchange"])

class TokenExchangeRequest(BaseModel):
    grant_type: str = "urn:ietf:params:oauth:grant-type:token-exchange"
    subject_token: str
    subject_token_type: str = "urn:ietf:params:oauth:token-type:access_token"
    audience: str = "novabank-api"
    scope: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    issued_token_type: str = "urn:ietf:params:oauth:token-type:access_token"
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str

@router.post("/oauth/token", response_model=TokenResponse)
@router.post("/api/v1/oauth/token", response_model=TokenResponse)
async def token_exchange_endpoint(
    request: Request,
):
    """
    RFC 8693 OAuth 2.0 Token Exchange implementation.
    Accepts application/x-www-form-urlencoded or application/json.
    """
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        grant_type = body.get("grant_type")
        subject_token = body.get("subject_token")
        audience = body.get("audience", settings.API_AUDIENCE)
        requested_scope = body.get("scope", "")
    else:
        form = await request.form()
        grant_type = form.get("grant_type")
        subject_token = form.get("subject_token")
        audience = form.get("audience", settings.API_AUDIENCE)
        requested_scope = form.get("scope", "")

    if grant_type != "urn:ietf:params:oauth:grant-type:token-exchange":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported grant_type: '{grant_type}'. Expected 'urn:ietf:params:oauth:grant-type:token-exchange'",
        )

    if not subject_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameter: 'subject_token'",
        )

    # 1. Validate subject_token
    try:
        claims = jwt.decode(
            subject_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid subject token: {str(e)}",
        )

    subject = claims.get("sub", "unknown")
    role = claims.get("role", "viewer")
    granted_scopes = claims.get("scope", "").split()

    # 2. Downscope verification
    ALLOWED_API_SCOPES = {"api:accounts:read", "api:cases:read", "api:payments:write", "api:incidents:write", "api:a2a:tasks"}
    
    if requested_scope:
        requested_scope_list = requested_scope.split()
    else:
        # Default downscoped API scopes
        requested_scope_list = ["api:accounts:read", "api:cases:read"]
        if role in ("agent", "admin", "service", "support_agent", "manager"):
            requested_scope_list.append("api:payments:write")

    # Scope downscoping: filter to allowed API scopes
    effective_scopes = [s for s in requested_scope_list if s in ALLOWED_API_SCOPES]
    if not effective_scopes:
        effective_scopes = ["api:accounts:read"]

    # 3. Mint exchanged API-audience token
    now = int(time.time())
    expires_in = 3600
    exchanged_claims = {
        "iss": settings.JWT_ISSUER,
        "sub": subject,
        "aud": audience,
        "role": role,
        "scope": " ".join(effective_scopes),
        "iat": now,
        "exp": now + expires_in,
        "act": {"sub": "rfc8693-token-exchange"},
    }
    access_token = jwt.encode(exchanged_claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return TokenResponse(
        access_token=access_token,
        issued_token_type="urn:ietf:params:oauth:token-type:access_token",
        token_type="Bearer",
        expires_in=expires_in,
        scope=" ".join(effective_scopes),
    )
