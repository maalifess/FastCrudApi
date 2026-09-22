from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class ItemDB(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="General", index=True)
    status = Column(String(50), default="pending", index=True)
    priority = Column(String(50), default="medium", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime, nullable=True, index=True)
    tags = Column(JSON, nullable=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    reminder_at = Column(DateTime, nullable=True)

    # Multi-user & workspace ownership (nullable for backwards compatibility)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    owner = relationship("UserDB", foreign_keys=[owner_id], back_populates="items")
    assignee = relationship("UserDB", foreign_keys=[assignee_id])
    workspace = relationship("WorkspaceDB", back_populates="items")
    comments = relationship("ItemCommentDB", back_populates="item", cascade="all, delete-orphan")
    activity = relationship("ItemActivityDB", back_populates="item", cascade="all, delete-orphan")

class ItemCommentDB(Base):
    __tablename__ = "item_comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    item = relationship("ItemDB", back_populates="comments")
    user = relationship("UserDB")

class ItemActivityDB(Base):
    __tablename__ = "item_activity"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False) # e.g., "created", "updated", "status_changed", "deleted", "restored"
    details = Column(JSON, nullable=True) # E.g., {"old_status": "pending", "new_status": "in_progress"}
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    item = relationship("ItemDB", back_populates="activity")
    user = relationship("UserDB")
