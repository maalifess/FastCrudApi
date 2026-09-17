import os
import csv
import io
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

import tempfile

# 1. Database Configuration with Environment Variables & Fallback
DATABASE_URL = os.getenv("DATABASE_URL")

def get_engine():
    if DATABASE_URL:
        if DATABASE_URL.startswith("mysql") or DATABASE_URL.startswith("mariadb"):
            return create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    # If explicit MariaDB environment variables are provided, try connecting
    if os.getenv("MARIADB_HOST") or os.getenv("MARIADB_DATABASE"):
        user = os.getenv("MARIADB_USER", "root")
        password = os.getenv("MARIADB_PASSWORD", "")
        host = os.getenv("MARIADB_HOST", "127.0.0.1")
        port = os.getenv("MARIADB_PORT", "3306")
        db_name = os.getenv("MARIADB_DATABASE", "fast_crud_db")
        mariadb_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
        try:
            eng = create_engine(mariadb_url, pool_pre_ping=True, pool_recycle=3600, connect_args={"connect_timeout": 3})
            with eng.connect():
                pass
            return eng
        except Exception as e:
            print(f"MariaDB connection failed ({e}). Falling back to SQLite.")

    # Fallback to SQLite (uses /tmp directory for Vercel serverless compatibility)
    db_file = os.path.join(tempfile.gettempdir(), "app_data.db")
    sqlite_url = f"sqlite:///{db_file}"
    return create_engine(sqlite_url, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Database Model
class ItemDB(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

try:
    Base.metadata.create_all(bind=engine)
except Exception as err:
    print(f"Database table setup note: {err}")

# 3. Pydantic Schemas
class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = ""

    class Config:
        from_attributes = True

# 4. Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="FastCRUD MariaDB API", version="1.1.0")

# Enable CORS for Flutter Web, Desktop, and Mobile Apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. CRUD Endpoints

@app.get("/")
def read_root():
    return {"status": "online", "message": "FastCRUD MariaDB API Server", "version": "1.1.0"}

# READ ALL with Search Query
@app.get("/items", response_model=List[ItemResponse])
def get_items(q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ItemDB)
    if q:
        search_filter = f"%{q}%"
        query = query.filter((ItemDB.title.like(search_filter)) | (ItemDB.description.like(search_filter)))
    return query.all()

# READ SINGLE
@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

# CREATE
@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = ItemDB(title=item.title, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# UPDATE
@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, updated: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db_item.title = updated.title
    db_item.description = updated.description
    db.commit()
    db.refresh(db_item)
    return db_item

# DELETE
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return None

# EXPORT DATA (CSV or JSON)
@app.get("/items/export")
def export_items(format: str = Query("csv", pattern="^(csv|json)$"), db: Session = Depends(get_db)):
    items = db.query(ItemDB).all()
    
    if format == "json":
        data = [{"id": item.id, "title": item.title, "description": item.description or ""} for item in items]
        return data
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "title", "description"])
    for item in items:
        writer.writerow([item.id, item.title, item.description or ""])
    
    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=items_export.csv"}
    )