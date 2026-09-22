import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.db.database import Base

class ItemDB(Base):
    __tablename__ = "items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
