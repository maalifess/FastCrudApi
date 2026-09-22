import os
import uuid
from typing import List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.orm import sessionmaker, declarative_base

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://")
if DATABASE_URL and DATABASE_URL.startswith("mariadb://"):
    DATABASE_URL = DATABASE_URL.replace("mariadb://", "mysql+pymysql://")
if DATABASE_URL and "?ssl-mode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?ssl-mode=")[0]
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./fastcrud.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class ItemDB(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

# Schemas
class ItemCreate(BaseModel):
    title: str

class ItemUpdate(BaseModel):
    title: str

class ItemResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# FastAPI App
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Barebones API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/api/v1/items", response_model=List[ItemResponse])
def get_items():
    db = SessionLocal()
    try:
        return db.query(ItemDB).order_by(ItemDB.created_at.desc()).all()
    finally:
        db.close()

@app.post("/api/v1/items", response_model=ItemResponse)
def create_item(item: ItemCreate):
    db = SessionLocal()
    try:
        db_item = ItemDB(title=item.title)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    finally:
        db.close()

@app.put("/api/v1/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemUpdate):
    db = SessionLocal()
    try:
        db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        db_item.title = item.title
        db.commit()
        db.refresh(db_item)
        return db_item
    finally:
        db.close()

@app.delete("/api/v1/items/{item_id}")
def delete_item(item_id: int):
    db = SessionLocal()
    try:
        db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        db.delete(db_item)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "ok"}