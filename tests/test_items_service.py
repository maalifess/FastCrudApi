import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_and_fetch_item_v1():
    # 1. Create item via /api/v1/items
    create_res = client.post("/api/v1/items", json={
        "title": "Alembic Database Migration Task",
        "description": "Verify Alembic initial schema creation",
        "category": "Backend",
        "status": "in_progress",
        "priority": "high"
    })
    assert create_res.status_code == 201
    created_item = create_res.json()
    assert created_item["title"] == "Alembic Database Migration Task"
    assert created_item["priority"] == "high"
    item_id = created_item["id"]

    # 2. Fetch single item via /api/v1/items/{id}
    fetch_res = client.get(f"/api/v1/items/{item_id}")
    assert fetch_res.status_code == 200
    assert fetch_res.json()["id"] == item_id

    # 3. Analytics summary via /api/v1/analytics/summary
    analytics_res = client.get("/api/v1/analytics/summary")
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["total_items"] >= 1
    assert analytics_data["high_priority_count"] >= 1

    # 4. Delete item via /api/v1/items/{id}
    del_res = client.delete(f"/api/v1/items/{item_id}")
    assert del_res.status_code == 204
