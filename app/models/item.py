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

    # Multi-user & workspace ownership (nullable for backwards compatibility)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    owner = relationship("UserDB", back_populates="items")
    workspace = relationship("WorkspaceDB", back_populates="items")
