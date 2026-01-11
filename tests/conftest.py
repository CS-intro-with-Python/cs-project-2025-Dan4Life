import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import create_app, get_db_connection


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE entry_tags, tags, entries, users RESTART IDENTITY CASCADE")
            conn.commit()
    yield
