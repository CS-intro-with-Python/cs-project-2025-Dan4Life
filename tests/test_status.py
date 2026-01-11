
def test_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json == {"ok": True}
