from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ItemCreate(BaseModel):
    title: str

class ItemResponse(BaseModel):
    id: str
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
