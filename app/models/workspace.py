"""
Workspace and WorkspaceMember database models for multi-tenant RBAC.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class WorkspaceDB(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("UserDB", back_populates="owned_workspaces")
    members = relationship("WorkspaceMemberDB", back_populates="workspace", cascade="all, delete-orphan", lazy="selectin")
    items = relationship("ItemDB", back_populates="workspace", lazy="selectin")

    def __repr__(self):
        return f"<WorkspaceDB(id={self.id}, slug='{self.slug}')>"


class WorkspaceMemberDB(Base):
    __tablename__ = "workspace_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False, default="member")  # owner, admin, member, viewer
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workspace = relationship("WorkspaceDB", back_populates="members")
    user = relationship("UserDB", back_populates="workspace_memberships")

    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    def __repr__(self):
        return f"<WorkspaceMemberDB(workspace={self.workspace_id}, user={self.user_id}, role='{self.role}')>"
