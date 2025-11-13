import requests

def test_health():
    r = requests.get("http://localhost:5000/api/health", timeout=2)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
