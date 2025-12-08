from fastapi.testclient import TestClient
from inference.api import app

client = TestClient(app)

def test_metrics_endpoint():
    # trigger at least one generate call to increment metrics
    payload = {
        "title": "Test Product",
        "description": "Amazing product.",
        "category": "electronics",
    }
    r = client.post("/generate", json=payload)
    assert r.status_code == 200

    # now check metrics
    m = client.get("/metrics")
    assert m.status_code == 200
    body = m.text
    assert "adgen_requests_total" in body
    assert "adgen_request_latency_seconds" in body
