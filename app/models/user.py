"""
User database model.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(150), nullable=False)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owned_workspaces = relationship("WorkspaceDB", back_populates="owner", lazy="selectin")
    workspace_memberships = relationship("WorkspaceMemberDB", back_populates="user", lazy="selectin")
    items = relationship("ItemDB", foreign_keys="[ItemDB.owner_id]", back_populates="owner", lazy="selectin")

    def __repr__(self):
        return f"<UserDB(id={self.id}, email='{self.email}')>"
