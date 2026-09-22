"""
FastAPI dependencies for authentication and RBAC authorization.
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import UserDB
from app.core.security import decode_token


# HTTP Bearer token extractor
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> UserDB:
    """
    Extract and validate JWT from Authorization header.
    Returns the authenticated user or raises 401.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use an access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(UserDB).filter(UserDB.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: UserDB = Depends(get_current_user),
) -> UserDB:
    """Ensure the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Optional[UserDB]:
    """
    Optionally extract user from token. Returns None if no token is provided.
    Used for endpoints that work both authenticated and anonymously.
    """
    if credentials is None:
        return None

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    return db.query(UserDB).filter(UserDB.id == int(user_id)).first()


def require_role(allowed_roles: List[str]):
    """
    Factory dependency: restrict endpoint to users with specific workspace roles.
    Usage: Depends(require_role(["owner", "admin"]))
    
    NOTE: This checks the role from `workspace_id` query/path param.
    Endpoints using this must accept a `workspace_id` parameter.
    """
    async def role_checker(
        workspace_id: int,
        current_user: UserDB = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        from app.models.workspace import WorkspaceMemberDB
        membership = (
            db.query(WorkspaceMemberDB)
            .filter(
                WorkspaceMemberDB.workspace_id == workspace_id,
                WorkspaceMemberDB.user_id == current_user.id,
            )
            .first()
        )
        if not membership or membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker
