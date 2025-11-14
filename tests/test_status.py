import requests

def test_status():
    r = requests.get("http://localhost:8080/api/status")
    assert r.status_code == 200