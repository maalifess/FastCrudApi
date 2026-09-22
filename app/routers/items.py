from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Response, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.item_service import ItemService
from app.core.dependencies import get_optional_user, get_current_user
from app.models.user import UserDB
from app.schemas.item_schemas import (
    ItemCreate,
    ItemUpdate,
    ItemResponse,
    PaginatedItemResponse,
    AnalyticsSummary,
    ItemCommentCreate,
    ItemCommentResponse,
    ItemActivityResponse,
)

router = APIRouter(tags=["Items & Analytics"])

@router.get("/analytics/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    return service.get_analytics(owner_id=owner_id)

@router.get("/items/export")
def export_items(
    format: str = Query("csv", pattern="^(csv|json)$"),
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    content, media_type = service.export_items(format=format, category=category, status=status, owner_id=owner_id)
    
    if media_type == "application/json":
        return content

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": "attachment; filename=items_export.csv"},
    )

@router.get("/items", response_model=List[ItemResponse])
def get_items(
    q: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    page: Optional[int] = Query(None, ge=1),
    limit: Optional[int] = Query(None, ge=1, le=100),
    sort_by: Optional[str] = "id",
    order: Optional[str] = "desc",
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    return service.list_items(
        q=q,
        category=category,
        status=status,
        priority=priority,
        page=page,
        limit=limit,
        sort_by=sort_by or "id",
        order=order or "desc",
        owner_id=owner_id,
    )

@router.get("/items/trash", response_model=List[ItemResponse])
def get_trash(
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    items = service.list_items(owner_id=owner_id, include_deleted=True)
    # Filter only deleted items
    return [item for item in items if item.deleted_at is not None]

@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    item = service.get_by_id(item_id, owner_id=owner_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item

@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item: ItemCreate,
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    return service.create_item(item, owner_id=owner_id)

@router.put("/items/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    updated: ItemUpdate,
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    item = service.update_item(item_id, updated, owner_id=owner_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    success = service.delete_item(item_id, owner_id=owner_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return None

@router.post("/items/{item_id}/restore", response_model=ItemResponse)
def restore_item(
    item_id: int,
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    success = service.restore_item(item_id, owner_id=owner_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or not in trash")
    return service.get_by_id(item_id, owner_id=owner_id)

@router.delete("/items/{item_id}/force", status_code=status.HTTP_204_NO_CONTENT)
def force_delete_item(
    item_id: int,
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    success = service.delete_item(item_id, owner_id=owner_id, force=True)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return None

@router.get("/items/{item_id}/comments", response_model=List[ItemCommentResponse])
def get_comments(
    item_id: int,
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    item = service.get_by_id(item_id, owner_id=owner_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return service.get_comments(item_id)

@router.post("/items/{item_id}/comments", response_model=ItemCommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    item_id: int,
    comment: ItemCommentCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id
    item = service.get_by_id(item_id, owner_id=owner_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return service.add_comment(item_id, current_user.id, comment)

@router.get("/items/{item_id}/activity", response_model=List[ItemActivityResponse])
def get_activity(
    item_id: int,
    current_user: Optional[UserDB] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    owner_id = current_user.id if current_user else None
    item = service.get_by_id(item_id, owner_id=owner_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return service.get_activity(item_id)
