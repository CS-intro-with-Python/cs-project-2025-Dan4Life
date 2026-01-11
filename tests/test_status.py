
from server import create_app, get_db_connection


def clean_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE entry_tags, tags, entries, users RESTART IDENTITY CASCADE")
            conn.commit()


def test_status():
    clean_db()
    app = create_app()
    client = app.test_client()
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json == {"ok": True}
