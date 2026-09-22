from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    category: Optional[str] = "General"
    status: Optional[str] = "pending"
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = []

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None

class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = ""
    category: str = "General"
    status: str = "pending"
    priority: str = "medium"
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaginatedItemResponse(BaseModel):
    items: List[ItemResponse]
    total: int
    page: int
    limit: int
    total_pages: int

class AnalyticsSummary(BaseModel):
    total_items: int
    pending_count: int
    in_progress_count: int
    completed_count: int
    high_priority_count: int
    category_counts: Dict[str, int]
