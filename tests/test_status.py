import requests

def test_status():
    r = requests.get("http://localhost:8080/api/status") 
    
    # Assert that the status code is 200 (OK)
    assert r.status_code == 200