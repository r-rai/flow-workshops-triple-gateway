import time
import json
import urllib.parse
from typing import Optional, Dict, Any, Set
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from jose import jwt, JWTError
from src.core.config import settings
from src.core.security import extract_delegation_chain

router = APIRouter(prefix="", tags=["OAuth2 & RFC 8693 Token Exchange"])

class TokenResponse(BaseModel):
    access_token: str
    issued_token_type: str = "urn:ietf:params:oauth:token-type:access_token"
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str

# Entitlement matrix: Maximum permitted target API scopes per subject role
ROLE_ENTITLED_SCOPES: Dict[str, Set[str]] = {
    "viewer": {"api:accounts:read", "api:cases:read"},
    "auditor": {"api:accounts:read", "api:cases:read"},
    "support_agent": {"api:accounts:read", "api:cases:read", "api:payments:write"},
    "teller": {"api:accounts:read", "api:cases:read", "api:payments:write"},
    "operator": {"api:accounts:read", "api:cases:read"},
    "agent": {"api:accounts:read", "api:cases:read", "api:payments:write", "api:a2a:tasks"},
    "payments_agent": {"api:accounts:read", "api:cases:read", "api:payments:write", "api:a2a:tasks"},
    "negotiator_bot": {"api:accounts:read", "api:cases:read", "api:a2a:tasks"},
    "manager": {"api:accounts:read", "api:cases:read", "api:payments:write", "api:a2a:tasks"},
    "admin": {"api:accounts:read", "api:cases:read", "api:payments:write", "api:incidents:write", "api:a2a:tasks"},
    "service": {"api:accounts:read", "api:cases:read", "api:payments:write", "api:a2a:tasks"},
}

VALID_TOKEN_TYPES = {
    "urn:ietf:params:oauth:token-type:access_token",
    "urn:ietf:params:oauth:token-type:jwt",
}

VALID_SUBJECT_AUDIENCES = {
    "novabank-mcp",
    "novabank-api",
    "novabank-auth",
}

VALID_TARGET_AUDIENCES = {
    settings.API_AUDIENCE,
    "novabank-api",
}

@router.post("/oauth/token", response_model=TokenResponse)
@router.post("/api/v1/oauth/token", response_model=TokenResponse)
async def token_exchange_endpoint(request: Request):
    """
    RFC 8693 OAuth 2.0 Token Exchange implementation.
    Accepts application/x-www-form-urlencoded (standard) or application/json.
    """
    content_type = request.headers.get("content-type", "").lower()
    raw_body = await request.body()

    grant_type = None
    subject_token = None
    subject_token_type = None
    audience = None
    requested_scope = None

    if "application/json" in content_type:
        try:
            body = json.loads(raw_body.decode("utf-8") if raw_body else "{}")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed JSON body",
            )
        grant_type = body.get("grant_type")
        subject_token = body.get("subject_token")
        subject_token_type = body.get("subject_token_type")
        audience = body.get("audience")
        requested_scope = body.get("scope")
    else:
        # Default / application/x-www-form-urlencoded (RFC 8693 §2.1)
        # Parse using standard library urllib.parse to avoid python-multipart dependency
        try:
            raw_str = raw_body.decode("utf-8") if raw_body else ""
            parsed = urllib.parse.parse_qs(raw_str, keep_blank_values=True)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed urlencoded form body",
            )
        grant_type = parsed.get("grant_type", [None])[0]
        subject_token = parsed.get("subject_token", [None])[0]
        subject_token_type = parsed.get("subject_token_type", [None])[0]
        audience = parsed.get("audience", [None])[0]
        requested_scope = parsed.get("scope", [None])[0]

    # 1. Validate RFC 8693 required request parameters
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

    if not subject_token_type or subject_token_type not in VALID_TOKEN_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing or unsupported 'subject_token_type': '{subject_token_type}'. Supported types: {sorted(VALID_TOKEN_TYPES)}",
        )

    target_audience = audience or settings.API_AUDIENCE
    if target_audience not in VALID_TARGET_AUDIENCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported target audience: '{target_audience}'. Supported: {sorted(VALID_TARGET_AUDIENCES)}",
        )

    # 2. Decode and validate subject_token
    try:
        claims = jwt.decode(
            subject_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            options={"verify_aud": False},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid subject token: {str(e)}",
        )

    # Validate incoming delegation provenance and depth (fail-closed if depth > 20)
    extract_delegation_chain(claims)

    subject = claims.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject token: missing 'sub' claim",
        )

    token_aud = claims.get("aud")
    if not token_aud or token_aud not in VALID_SUBJECT_AUDIENCES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid subject token: invalid or untrusted audience '{token_aud}'",
        )

    # 3. Entitlement & Scope Downscoping Validation
    role = claims.get("role", "viewer")
    max_entitled = ROLE_ENTITLED_SCOPES.get(role, {"api:accounts:read", "api:cases:read"})
    granted_scopes = set(claims.get("scope", "").split())

    if token_aud == "novabank-mcp":
        # MCP token exchanging for API execution
        # Verify caller has MCP execution authorization
        if not ({"mcp:tools", "tools:call"}.intersection(granted_scopes) or role in ("agent", "payments_agent", "service", "admin")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Subject token lacks MCP tool execution authorization",
            )
        authorized_scopes = max_entitled
    else:
        # Pre-existing API or auth token: cannot escalate beyond already granted scopes
        authorized_scopes = granted_scopes.intersection(max_entitled)

    # Process requested scopes
    if requested_scope:
        req_set = set(requested_scope.split())
        unauthorized = req_set - authorized_scopes
        if unauthorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requested scope not authorized for subject: {sorted(unauthorized)}",
            )
        effective_scopes = req_set
    else:
        # Default safe downscoped subset
        effective_scopes = {"api:accounts:read", "api:cases:read"}.intersection(authorized_scopes)
        if not effective_scopes:
            effective_scopes = authorized_scopes

    if not effective_scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subject has no authorized scopes for the target audience",
        )

    # 4. Mint exchanged API-audience token with preserved delegation context (RFC 8693 §4.1)
    now = int(time.time())
    expires_in = 3600

    existing_act = claims.get("act")
    delegated_by = claims.get("delegated_by")

    # Preserve delegation provenance across single and repeated exchanges
    if existing_act and isinstance(existing_act, dict):
        if existing_act.get("sub") == subject:
            act_claim = existing_act
        else:
            act_claim = {"sub": subject, "act": existing_act}
    else:
        act_claim = {"sub": subject}

    # Validate that resulting delegation chain does not exceed maximum depth
    extract_delegation_chain({"act": act_claim, "delegated_by": delegated_by})

    exchanged_claims: Dict[str, Any] = {
        "iss": settings.JWT_ISSUER,
        "sub": subject,
        "aud": target_audience,
        "role": role,
        "scope": " ".join(sorted(effective_scopes)),
        "iat": now,
        "exp": now + expires_in,
        "act": act_claim,
    }
    if delegated_by:
        exchanged_claims["delegated_by"] = delegated_by

    access_token = jwt.encode(exchanged_claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return TokenResponse(
        access_token=access_token,
        issued_token_type="urn:ietf:params:oauth:token-type:access_token",
        token_type="Bearer",
        expires_in=expires_in,
        scope=" ".join(sorted(effective_scopes)),
    )
