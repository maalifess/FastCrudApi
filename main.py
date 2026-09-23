import os
from typing import List
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base, Session

db_url = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite")
db_url = db_url.replace("mysql://", "mysql+pymysql://")
db_url = db_url.replace("mariadb://", "mysql+pymysql://")
db_url = db_url.split("?")[0]

if "sqlite" in db_url:
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(db_url)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class ItemModel(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    title = Column(String(255))

Base.metadata.create_all(bind=engine)

class ItemCreate(BaseModel):
    title: str

class ItemResponse(BaseModel):
    id: int
    title: str
    class Config:
        from_attributes = True

app = FastAPI()
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/items", response_model=List[ItemResponse])
def get_all_items(db: Session = Depends(get_db)):
    return db.query(ItemModel).order_by(ItemModel.id.desc()).all()

@app.post("/api/v1/items", response_model=ItemResponse)
def create_new_item(item_data: ItemCreate, db: Session = Depends(get_db)):
    new_item = ItemModel(title=item_data.title)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.put("/api/v1/items/{item_id}", response_model=ItemResponse)
def update_existing_item(item_id: int, item_data: ItemCreate, db: Session = Depends(get_db)):
    db.query(ItemModel).filter(ItemModel.id == item_id).update({"title": item_data.title})
    db.commit()
    return db.query(ItemModel).filter(ItemModel.id == item_id).first()

@app.delete("/api/v1/items/{item_id}")
def delete_existing_item(item_id: int, db: Session = Depends(get_db)):
    db.query(ItemModel).filter(ItemModel.id == item_id).delete()
    db.commit()
    return {"status": "success"}