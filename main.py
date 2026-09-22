import os
from typing import List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# DB Setup
db_url = os.getenv("DATABASE_URL", "sqlite:///./fastcrud.db")
db_url = db_url.replace("mysql://", "mysql+pymysql://").replace("mariadb://", "mysql+pymysql://").split("?ssl-mode=")[0]
engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# DB Model
class ItemDB(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

# Schemas
class ItemIn(BaseModel):
    title: str

class ItemOut(ItemIn):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# App Setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/api/v1/items", response_model=List[ItemOut])
def get_items(db: Session = Depends(get_db)):
    return db.query(ItemDB).order_by(ItemDB.created_at.desc()).all()

@app.post("/api/v1/items", response_model=ItemOut)
def create_item(item: ItemIn, db: Session = Depends(get_db)):
    db_item = ItemDB(title=item.title)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/api/v1/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, item: ItemIn, db: Session = Depends(get_db)):
    db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if not db_item: raise HTTPException(404, "Not found")
    db_item.title = item.title
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/api/v1/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if not db_item: raise HTTPException(404, "Not found")
    db.delete(db_item)
    db.commit()
    return {"status": "ok"}