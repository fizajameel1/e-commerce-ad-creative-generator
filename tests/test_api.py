from fastapi.testclient import TestClient
from inference.api import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_generate_ads():
    payload = {
        "title": "Test Product",
        "description": "This is an amazing product.",
        "category": "electronics"
    }
    r = client.post("/generate", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "creatives" in data
    assert len(data["creatives"]) == 3
    # check strings are non-empty
    for c in data["creatives"]:
        assert isinstance(c, str) and len(c) > 10
