"""
Pydantic schemas for authentication and user management.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserRegister(BaseModel):
    """Registration request."""
    email: str = Field(..., min_length=5, max_length=255, description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    display_name: str = Field(..., min_length=1, max_length=150, description="Display name")


class UserLogin(BaseModel):
    """Login request."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")


class TokenRefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserResponse(BaseModel):
    """Public user profile response."""
    id: int
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User profile update request."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=150)
    avatar_url: Optional[str] = None


class WorkspaceCreate(BaseModel):
    """Create workspace request."""
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200, pattern=r"^[a-z0-9\-]+$")
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    """Workspace response."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    owner_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkspaceMemberResponse(BaseModel):
    """Workspace member response."""
    id: int
    workspace_id: int
    user_id: int
    role: str
    joined_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkspaceInvite(BaseModel):
    """Invite a user to a workspace."""
    email: str = Field(..., description="Email of user to invite")
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")
