import time
from typing import Dict, Any, List, Optional
from fastapi import Header, HTTPException, Depends, status
from jose import jwt, JWTError
from src.core.config import settings

class Principal:
    def __init__(
        self,
        id: str,
        role: str,
        scopes: List[str],
        delegated_by: Optional[str] = None,
        delegation_chain: Optional[List[str]] = None,
        auth_method: str = "bearer"
    ):
        self.id = id
        self.role = role
        self.scopes = scopes
        self.delegation_chain = delegation_chain or []
        if delegated_by:
            self.delegated_by = delegated_by
        elif self.delegation_chain:
            self.delegated_by = self.delegation_chain[-1]
        else:
            self.delegated_by = None
        self.auth_method = auth_method

    def has_in_delegation_chain(self, principal_id: str) -> bool:
        return principal_id in self.delegation_chain

MAX_DELEGATION_DEPTH = 20

def extract_delegation_chain(claims: Dict[str, Any]) -> List[str]:
    """
    Normalizes and extracts the complete delegation chain from JWT claims.
    Handles direct `delegated_by`, nested RFC 8693 `act` claims, and repeated exchanges.
    Rejects over-depth chains (> MAX_DELEGATION_DEPTH) instead of silently truncating them.
    """
    chain: List[str] = []

    # 1. Direct delegated_by claim (string or list)
    del_by = claims.get("delegated_by")
    if del_by:
        if isinstance(del_by, list):
            chain.extend(str(x) for x in del_by if x)
        elif isinstance(del_by, str) and del_by.strip():
            chain.append(del_by.strip())

    # 2. RFC 8693 §4.1 nested actor (act) claim
    curr = claims.get("act")
    depth = 0
    while isinstance(curr, dict):
        depth += 1
        if depth > MAX_DELEGATION_DEPTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Delegation chain exceeds maximum permitted depth of {MAX_DELEGATION_DEPTH}",
            )
        sub = curr.get("sub")
        if sub and isinstance(sub, str):
            chain.append(sub)
        curr = curr.get("act")

    # Preserve order of appearance, deduplicate
    seen = set()
    result = []
    for item in chain:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

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
            delegation_chain = extract_delegation_chain(claims)
            return Principal(
                id=sub,
                role=role,
                scopes=scopes,
                delegation_chain=delegation_chain,
                auth_method="bearer"
            )
        except HTTPException:
            raise
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
                scopes=["api:accounts:read", "api:cards:read", "api:cards:write", "api:payments:write", "api:cases:read", "api:cases:write", "api:incidents:write"],
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
    delegated_by: Optional[str] = None,
    act: Optional[Dict[str, Any]] = None,
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
    if act:
        claims["act"] = act
    elif delegated_by:
        claims["act"] = {"sub": delegated_by}
    if delegated_by:
        claims["delegated_by"] = delegated_by
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

