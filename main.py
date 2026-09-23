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
# Create the engine to talk to the database
if "sqlite" in db_url:
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(db_url)

# Create a session factory
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ====================================================================
# 2. Database Models (SQL Tables)
# ====================================================================

class ItemModel(Base):
    """This represents the actual table in our database."""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255))


# Create the tables in the database if they don't exist
Base.metadata.create_all(bind=engine)


# ====================================================================
# 3. Pydantic Models (Data Validation for API)
# ====================================================================

class ItemCreate(BaseModel):
    """Data required to create a new item."""
    title: str

class ItemResponse(BaseModel):
    """Data returned to the client when requesting an item."""
    id: int
    title: str

    class Config:
        from_attributes = True


# ====================================================================
# 4. FastAPI Setup
# ====================================================================

app = FastAPI()

# Allow connections from any frontend (CORS)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Helper function to get a database session and close it automatically
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ====================================================================
# 5. API Routes (Endpoints)
# ====================================================================

@app.get("/api/v1/items", response_model=List[ItemResponse])
def get_all_items(db: Session = Depends(get_db)):
    """Fetch all items from the database."""
    items = db.query(ItemModel).order_by(ItemModel.id.desc()).all()
    return items


@app.post("/api/v1/items", response_model=ItemResponse)
def create_new_item(item_data: ItemCreate, db: Session = Depends(get_db)):
    """Create a new item in the database."""
    new_item = ItemModel(title=item_data.title)
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return new_item


@app.put("/api/v1/items/{item_id}", response_model=ItemResponse)
def update_existing_item(item_id: int, item_data: ItemCreate, db: Session = Depends(get_db)):
    """Update the title of an existing item."""
    db.query(ItemModel).filter(ItemModel.id == item_id).update({"title": item_data.title})
    db.commit()
    
    updated_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    return updated_item


@app.delete("/api/v1/items/{item_id}")
def delete_existing_item(item_id: int, db: Session = Depends(get_db)):
    """Delete an item from the database."""
    db.query(ItemModel).filter(ItemModel.id == item_id).delete()
    db.commit()
    
    return {"status": "success"}