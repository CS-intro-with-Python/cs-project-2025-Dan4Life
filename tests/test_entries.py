
def register_user(client, username="alice", password="secret"):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 201
    return response.json


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_entry_flow(client):
    registration = register_user(client)
    token = registration["token"]

    entry_response = client.post(
        "/api/entries",
        headers=auth_headers(token),
        json={"title": "Day 1", "text": "Feeling calm", "tags": ["gratitude", "focus"]},
    )
    assert entry_response.status_code == 201
    entry = entry_response.json
    assert entry["title"] == "Day 1"
    assert "gratitude" in entry["tags"]
    assert entry["sentiment"] in {"positive", "neutral", "negative"}

    list_response = client.get("/api/entries", headers=auth_headers(token))
    assert list_response.status_code == 200
    assert len(list_response.json) == 1

    tag_response = client.get("/api/entries?tag=gratitude", headers=auth_headers(token))
    assert tag_response.status_code == 200
    assert len(tag_response.json) == 1

    dashboard_response = client.get("/api/dashboard/summary", headers=auth_headers(token))
    assert dashboard_response.status_code == 200
    assert dashboard_response.json["total_entries"] == 1


def test_login_rejects_invalid_password(client):
    register_user(client, username="bob", password="secret")
    response = client.post(
        "/api/auth/login",
        json={"username": "bob", "password": "wrong"},
    )
    assert response.status_code == 401
