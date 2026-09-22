import csv
import io
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import or_, func, desc, asc
from sqlalchemy.orm import Session

from app.models.item import ItemDB
from app.schemas.item_schemas import ItemCreate, ItemUpdate, AnalyticsSummary

class ItemService:
    def __init__(self, db: Session):
        self.db = db

    def _apply_base_filters(self, query, owner_id: Optional[int] = None, include_deleted: bool = False):
        """Filter items by owner_id and exclude soft-deleted items by default."""
        if owner_id is not None:
            query = query.filter(
                or_(ItemDB.owner_id == owner_id, ItemDB.owner_id.is_(None))
            )
        if not include_deleted:
            query = query.filter(ItemDB.deleted_at.is_(None))
        return query

    def get_by_id(self, item_id: int, owner_id: Optional[int] = None, include_deleted: bool = False) -> Optional[ItemDB]:
        query = self.db.query(ItemDB).filter(ItemDB.id == item_id)
        query = self._apply_base_filters(query, owner_id, include_deleted)
        return query.first()

    def list_items(
        self,
        q: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        sort_by: str = "id",
        order: str = "desc",
        owner_id: Optional[int] = None,
        include_deleted: bool = False,
    ) -> List[ItemDB]:
        query = self.db.query(ItemDB)
        query = self._apply_base_filters(query, owner_id, include_deleted)

        if q:
            search_filter = f"%{q}%"
            query = query.filter(
                or_(
                    ItemDB.title.like(search_filter),
                    ItemDB.description.like(search_filter),
                    ItemDB.category.like(search_filter),
                )
            )
        if category:
            query = query.filter(ItemDB.category == category)
        if status:
            query = query.filter(ItemDB.status == status)
        if priority:
            query = query.filter(ItemDB.priority == priority)

        sort_column = getattr(ItemDB, sort_by, ItemDB.id)
        if order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        if page and limit:
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)

        return query.all()

    def create_item(self, data: ItemCreate, owner_id: Optional[int] = None) -> ItemDB:
        db_item = ItemDB(
            title=data.title,
            description=data.description,
            category=data.category or "General",
            status=data.status or "pending",
            priority=data.priority or "medium",
            owner_id=owner_id,
        )
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def update_item(self, item_id: int, data: ItemUpdate, owner_id: Optional[int] = None) -> Optional[ItemDB]:
        db_item = self.get_by_id(item_id, owner_id=owner_id)
        if not db_item:
            return None

        if data.title is not None:
            db_item.title = data.title
        if data.description is not None:
            db_item.description = data.description
        if data.category is not None:
            db_item.category = data.category
        if data.status is not None:
            db_item.status = data.status
        if data.priority is not None:
            db_item.priority = data.priority

        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def delete_item(self, item_id: int, owner_id: Optional[int] = None, force: bool = False) -> bool:
        db_item = self.get_by_id(item_id, owner_id=owner_id, include_deleted=True)
        if not db_item:
            return False

        if force:
            self.db.delete(db_item)
        else:
            from datetime import datetime
            db_item.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def restore_item(self, item_id: int, owner_id: Optional[int] = None) -> bool:
        db_item = self.get_by_id(item_id, owner_id=owner_id, include_deleted=True)
        if not db_item or db_item.deleted_at is None:
            return False
            
        db_item.deleted_at = None
        self.db.commit()
        return True

    def get_analytics(self, owner_id: Optional[int] = None) -> AnalyticsSummary:
        base_query = self.db.query(ItemDB)
        base_query = self._apply_base_filters(base_query, owner_id)

        total = base_query.count()
        pending = base_query.filter(ItemDB.status == "pending").count()
        in_progress = base_query.filter(ItemDB.status == "in_progress").count()
        completed = base_query.filter(ItemDB.status == "completed").count()
        high_priority = base_query.filter(ItemDB.priority == "high").count()

        # Need fresh subquery for group_by
        cat_query = self.db.query(ItemDB.category, func.count(ItemDB.id))
        cat_query = self._apply_base_filters(cat_query, owner_id)
        cat_results = cat_query.group_by(ItemDB.category).all()
        category_counts = {cat or "General": cnt for cat, cnt in cat_results}

        return AnalyticsSummary(
            total_items=total,
            pending_count=pending,
            in_progress_count=in_progress,
            completed_count=completed,
            high_priority_count=high_priority,
            category_counts=category_counts,
        )

    def export_items(
        self,
        format: str = "csv",
        category: Optional[str] = None,
        status: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> Tuple[Any, str]:
        items = self.list_items(category=category, status=status, owner_id=owner_id)

        if format == "json":
            data = [
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description or "",
                    "category": item.category or "General",
                    "status": item.status or "pending",
                    "priority": item.priority or "medium",
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                }
                for item in items
            ]
            return data, "application/json"

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "description", "category", "status", "priority", "created_at"])
        for item in items:
            writer.writerow([
                item.id,
                item.title,
                item.description or "",
                item.category or "General",
                item.status or "pending",
                item.priority or "medium",
                item.created_at.isoformat() if item.created_at else "",
            ])

        return output.getvalue(), "text/csv"
