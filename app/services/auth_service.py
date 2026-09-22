"""
Authentication business logic: register, login, token refresh, user lookup.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import UserDB
from app.models.workspace import WorkspaceDB, WorkspaceMemberDB
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import settings


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[UserDB]:
        """Find a user by email (case-insensitive)."""
        return self.db.query(UserDB).filter(UserDB.email == email.lower().strip()).first()

    def get_user_by_id(self, user_id: int) -> Optional[UserDB]:
        """Find a user by ID."""
        return self.db.query(UserDB).filter(UserDB.id == user_id).first()

    def register(self, email: str, password: str, display_name: str) -> UserDB:
        """
        Register a new user. Creates a personal workspace automatically.
        Raises ValueError if email is already taken.
        """
        email = email.lower().strip()

        existing = self.get_user_by_email(email)
        if existing:
            raise ValueError("An account with this email already exists")

        user = UserDB(
            email=email,
            hashed_password=hash_password(password),
            display_name=display_name.strip(),
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        self.db.flush()  # Get user.id before creating workspace

        # Create a personal workspace for the user
        slug = f"personal-{user.id}"
        workspace = WorkspaceDB(
            name=f"{display_name.strip()}'s Workspace",
            slug=slug,
            description="Personal workspace",
            owner_id=user.id,
        )
        self.db.add(workspace)
        self.db.flush()

        # Add the user as workspace owner
        membership = WorkspaceMemberDB(
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> Optional[UserDB]:
        """Verify email and password. Returns user if valid, None otherwise."""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def create_tokens(self, user: UserDB) -> dict:
        """Generate access + refresh token pair for a user."""
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    def refresh_tokens(self, refresh_token: str) -> Optional[dict]:
        """
        Validate a refresh token and issue a new token pair.
        Returns None if the refresh token is invalid/expired.
        """
        payload = decode_token(refresh_token)
        if not payload:
            return None
        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = self.get_user_by_id(int(user_id))
        if not user or not user.is_active:
            return None

        return self.create_tokens(user)

    def get_user_workspaces(self, user_id: int):
        """Get all workspaces the user is a member of."""
        memberships = (
            self.db.query(WorkspaceMemberDB)
            .filter(WorkspaceMemberDB.user_id == user_id)
            .all()
        )
        workspace_ids = [m.workspace_id for m in memberships]
        return self.db.query(WorkspaceDB).filter(WorkspaceDB.id.in_(workspace_ids)).all()

    def get_user_role_in_workspace(self, user_id: int, workspace_id: int) -> Optional[str]:
        """Get the role of a user in a specific workspace. Returns None if not a member."""
        membership = (
            self.db.query(WorkspaceMemberDB)
            .filter(
                WorkspaceMemberDB.user_id == user_id,
                WorkspaceMemberDB.workspace_id == workspace_id,
            )
            .first()
        )
        return membership.role if membership else None
