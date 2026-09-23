import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base, Session

url = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite").replace("mysql://", "mysql+pymysql://").replace("mariadb://", "mysql+pymysql://").split("?")[0]
engine = create_engine(url, connect_args={"check_same_thread": False} if "sqlite" in url else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    title = Column(String(255))

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

class In(BaseModel): title: str

@app.get("/api/v1/items")
def _(db: Session = Depends(get_db)): return db.query(Item).order_by(Item.id.desc()).all()

@app.post("/api/v1/items")
def _(i: In, db: Session = Depends(get_db)):
    db.add(item := Item(title=i.title))
    db.commit()
    db.refresh(item)
    return item

@app.put("/api/v1/items/{id}")
def _(id: int, i: In, db: Session = Depends(get_db)):
    db.query(Item).filter(Item.id == id).update({"title": i.title})
    db.commit()
    return db.query(Item).filter(Item.id == id).first()

@app.delete("/api/v1/items/{id}")
def _(id: int, db: Session = Depends(get_db)):
    db.query(Item).filter(Item.id == id).delete()
    db.commit()