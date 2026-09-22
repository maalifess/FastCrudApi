from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.item import ItemDB
from app.schemas.item_schemas import ItemCreate, ItemResponse

router = APIRouter(prefix="/items", tags=["Items"])

@router.get("", response_model=List[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return db.query(ItemDB).order_by(ItemDB.created_at.desc()).all()

@router.post("", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = ItemDB(title=item.title)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}")
def delete_item(item_id: str, db: Session = Depends(get_db)):
    item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"status": "ok"}
