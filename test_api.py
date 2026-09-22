from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api():
    # 1. Root health check
    res = client.get("/")
    assert res.status_code == 200
    print("[OK] Health check Passed:", res.json())

    # 2. Create items with categories, status, priority
    item1 = client.post("/api/items", json={
        "title": "Design Database Schema",
        "description": "Create MariaDB tables and indexes",
        "category": "Engineering",
        "status": "in_progress",
        "priority": "high"
    })
    assert item1.status_code == 201
    item1_data = item1.json()
    print("[OK] Create Item 1 Passed:", item1_data)

    item2 = client.post("/api/items", json={
        "title": "Build Flutter UI Dashboard",
        "description": "Implement modern Material 3 stats cards and filter chips",
        "category": "Frontend",
        "status": "pending",
        "priority": "medium"
    })
    assert item2.status_code == 201
    print("[OK] Create Item 2 Passed:", item2.json())

    # 3. Analytics summary
    analytics = client.get("/api/analytics/summary")
    assert analytics.status_code == 200
    analytics_data = analytics.json()
    print("[OK] Analytics Summary Passed:", analytics_data)
    assert analytics_data["total_items"] >= 2
    assert analytics_data["high_priority_count"] >= 1

    # 4. Filter by status
    in_prog = client.get("/api/items?status=in_progress")
    assert in_prog.status_code == 200
    assert len(in_prog.json()) >= 1
    print("[OK] Filter by Status Passed (in_progress items):", len(in_prog.json()))

    # 5. Search query
    search_res = client.get("/api/items?q=Flutter")
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1
    print("[OK] Search Query Passed (q=Flutter):", search_res.json()[0]["title"])

    # 6. Export CSV
    export_csv = client.get("/api/items/export?format=csv")
    assert export_csv.status_code == 200
    assert "id,title,description" in export_csv.text
    print("[OK] Export CSV Passed")

    print("\nALL BACKEND API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_api()
