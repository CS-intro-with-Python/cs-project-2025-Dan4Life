from flask import Flask, jsonify, request, render_template, make_response, send_from_directory
from flasgger import Swagger
from werkzeug.security import generate_password_hash, check_password_hash
import os
import time
import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, date
from functools import wraps
import csv
import io
from textblob import TextBlob
import markdown
import bleach
from werkzeug.utils import secure_filename
import imghdr

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")

ALLOWED_IMAGE_TYPES = {"jpeg", "png", "gif", "webp"}
ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "a",
    "img",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title"],
}


def get_db_config():
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "mindspace"),
        "user": os.getenv("POSTGRES_USER", "mindspace"),
        "password": os.getenv("POSTGRES_PASSWORD", "mindspace"),
    }


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    return psycopg2.connect(**get_db_config())


def init_db():
    retries = int(os.getenv("POSTGRES_INIT_RETRIES", "10"))
    delay = float(os.getenv("POSTGRES_INIT_DELAY", "1"))
    last_error = None
    for _ in range(retries):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            username TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            created_at TIMESTAMP NOT NULL DEFAULT NOW()
                        );
                        CREATE TABLE IF NOT EXISTS entries (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            title TEXT,
                            text TEXT NOT NULL,
                            sentiment TEXT,
                            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                        );
                        CREATE TABLE IF NOT EXISTS tags (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            name TEXT NOT NULL,
                            UNIQUE (user_id, name)
                        );
                        CREATE TABLE IF NOT EXISTS entry_tags (
                            entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
                            tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                            PRIMARY KEY (entry_id, tag_id)
                        );
                        """
                    )
                    conn.commit()
            return
        except psycopg2.OperationalError as exc:
            last_error = exc
            time.sleep(delay)
    if last_error is not None:
        raise last_error


def create_token(user_id, username):
    secret = os.getenv("JWT_SECRET", "dev-secret")
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=12),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token):
    secret = os.getenv("JWT_SECRET", "dev-secret")
    return jwt.decode(token, secret, algorithms=["HS256"])


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        token = header.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        user_id = payload.get("sub")
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, username, created_at FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 401
        request.user = user
        return fn(*args, **kwargs)

    return wrapper


def normalize_tags(raw_tags):
    tags = []
    for tag in raw_tags:
        clean = tag.strip().lower()
        if clean and clean not in tags:
            tags.append(clean[:50])
    return tags


def analyze_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity >= 0.2:
        return "positive"
    if polarity <= -0.2:
        return "negative"
    return "neutral"


def render_markdown(text):
    html = markdown.markdown(text or "", extensions=["extra"])
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=["http", "https", "data"],
        strip=True,
    )
    return cleaned


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    return UPLOAD_DIR


def attach_tags(conn, entries):
    entry_ids = [entry["id"] for entry in entries]
    if not entry_ids:
        return entries
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT et.entry_id, t.name
            FROM entry_tags et
            JOIN tags t ON t.id = et.tag_id
            WHERE et.entry_id = ANY(%s)
            ORDER BY t.name
            """,
            (entry_ids,),
        )
        rows = cur.fetchall()
    tag_map = {entry_id: [] for entry_id in entry_ids}
    for row in rows:
        tag_map[row["entry_id"]].append(row["name"])
    for entry in entries:
        entry["tags"] = tag_map.get(entry["id"], [])
    return entries


def create_app():
    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR,
        static_url_path="/static",
    )
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    if os.getenv("SKIP_DB_INIT") != "1":
        init_db()

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "MindSpace API",
            "description": "Private journaling API for MindSpace",
            "version": "1.0.0",
        },
        "basePath": "/",
    }
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/docs/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs/",
    }
    Swagger(app, template=swagger_template, config=swagger_config)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html")

    @app.route("/entries/<int:entry_id>")
    def entry_page(entry_id):
        return render_template("entry.html", entry_id=entry_id)

    @app.route("/api/status")
    def status():
        """Health check endpoint.
        ---
        responses:
          200:
            description: OK
        """
        return jsonify({"ok": True})

    @app.route("/api/auth/register", methods=["POST"])
    def register():
        """Register a new user.
        ---
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                username:
                  type: string
                password:
                  type: string
        responses:
          201:
            description: Created
          400:
            description: Validation error
        """
        data = request.json or {}
        username = (data.get("username") or "").strip().lower()
        password = data.get("password") or ""
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        password_hash = generate_password_hash(password)
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                try:
                    cur.execute(
                        "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, username, created_at",
                        (username, password_hash),
                    )
                    user = cur.fetchone()
                    conn.commit()
                except psycopg2.IntegrityError:
                    conn.rollback()
                    return jsonify({"error": "Username already exists"}), 400
        token = create_token(user["id"], user["username"])
        return jsonify({"user": user, "token": token}), 201

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        """Authenticate a user.
        ---
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                username:
                  type: string
                password:
                  type: string
        responses:
          200:
            description: OK
          401:
            description: Unauthorized
        """
        data = request.json or {}
        username = (data.get("username") or "").strip().lower()
        password = data.get("password") or ""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, username, password_hash, created_at FROM users WHERE username = %s", (username,))
                user = cur.fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid credentials"}), 401
        token = create_token(user["id"], user["username"])
        return jsonify(
            {
                "user": {"id": user["id"], "username": user["username"], "created_at": user["created_at"]},
                "token": token,
            }
        )

    @app.route("/api/me")
    @auth_required
    def me():
        """Get the current user profile.
        ---
        responses:
          200:
            description: OK
        """
        return jsonify({"user": request.user})

    @app.route("/api/entries", methods=["POST"])
    @auth_required
    def create_entry():
        """Create a journal entry.
        ---
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                title:
                  type: string
                text:
                  type: string
                tags:
                  type: array
                  items:
                    type: string
        responses:
          201:
            description: Created
        """
        data = request.json or {}
        title = (data.get("title") or "").strip()
        text = (data.get("text") or "").strip()
        raw_tags = data.get("tags") or []
        if not text:
            return jsonify({"error": "Text is required"}), 400
        tags = normalize_tags(raw_tags)
        sentiment = analyze_sentiment(text)
        rendered_html = render_markdown(text)
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO entries (user_id, title, text, sentiment)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, title, text, sentiment, created_at, updated_at
                    """,
                    (request.user["id"], title or None, text, sentiment),
                )
                entry = cur.fetchone()
                if tags:
                    for tag in tags:
                        cur.execute(
                            "INSERT INTO tags (user_id, name) VALUES (%s, %s) ON CONFLICT (user_id, name) DO NOTHING",
                            (request.user["id"], tag),
                        )
                    cur.execute(
                        "SELECT id, name FROM tags WHERE user_id = %s AND name = ANY(%s)",
                        (request.user["id"], tags),
                    )
                    tag_rows = cur.fetchall()
                    for tag_row in tag_rows:
                        cur.execute(
                            "INSERT INTO entry_tags (entry_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (entry["id"], tag_row["id"]),
                        )
                conn.commit()
                entry["tags"] = tags
                entry["rendered_html"] = rendered_html
        return jsonify(entry), 201

    @app.route("/api/entries", methods=["GET"])
    @auth_required
    def list_entries():
        """List journal entries.
        ---
        parameters:
          - in: query
            name: search
            type: string
          - in: query
            name: tag
            type: string
        responses:
          200:
            description: OK
        """
        search = (request.args.get("search") or "").strip()
        tag = (request.args.get("tag") or "").strip().lower()
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT id, title, text, sentiment, created_at, updated_at FROM entries WHERE user_id = %s"
                params = [request.user["id"]]
                if search:
                    query += " AND (title ILIKE %s OR text ILIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%"])
                if tag:
                    query += " AND id IN (SELECT et.entry_id FROM entry_tags et JOIN tags t ON t.id = et.tag_id WHERE t.user_id = %s AND t.name = %s)"
                    params.extend([request.user["id"], tag])
                query += " ORDER BY created_at DESC"
                cur.execute(query, params)
                entries = cur.fetchall()
            entries = attach_tags(conn, entries)
            for entry in entries:
                entry["rendered_html"] = render_markdown(entry.get("text"))
        return jsonify(entries)

    @app.route("/api/entries/<int:entry_id>", methods=["GET"])
    @auth_required
    def get_entry(entry_id):
        """Get a single journal entry.
        ---
        parameters:
          - in: path
            name: entry_id
            type: integer
            required: true
        responses:
          200:
            description: OK
          404:
            description: Not found
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, title, text, sentiment, created_at, updated_at
                    FROM entries
                    WHERE id = %s AND user_id = %s
                    """,
                    (entry_id, request.user["id"]),
                )
                entry = cur.fetchone()
            if not entry:
                return jsonify({"error": "Entry not found"}), 404
            entry = attach_tags(conn, [entry])[0]
            entry["rendered_html"] = render_markdown(entry.get("text"))
        return jsonify(entry)

    @app.route("/api/entries/<int:entry_id>", methods=["PUT"])
    @auth_required
    def update_entry(entry_id):
        """Update a journal entry.
        ---
        parameters:
          - in: path
            name: entry_id
            type: integer
            required: true
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                title:
                  type: string
                text:
                  type: string
                tags:
                  type: array
                  items:
                    type: string
        responses:
          200:
            description: OK
          404:
            description: Not found
        """
        data = request.json or {}
        raw_tags = data.get("tags")
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, title, text FROM entries WHERE id = %s AND user_id = %s",
                    (entry_id, request.user["id"]),
                )
                existing_entry = cur.fetchone()
                if not existing_entry:
                    return jsonify({"error": "Entry not found"}), 404
                title = data.get("title")
                text = data.get("text")
                if title is None:
                    title = existing_entry["title"]
                else:
                    title = title.strip() or None
                if text is None:
                    text = existing_entry["text"]
                else:
                    text = text.strip()
                    if not text:
                        return jsonify({"error": "Text is required"}), 400
                sentiment = analyze_sentiment(text)
                cur.execute(
                    """
                    UPDATE entries
                    SET title = %s, text = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, title, text, sentiment, created_at, updated_at
                    """,
                    (title or None, text or None, entry_id),
                )
                entry = cur.fetchone()
                entry["sentiment"] = sentiment
                entry["rendered_html"] = render_markdown(text)
                if raw_tags is not None:
                    tags = normalize_tags(raw_tags)
                    cur.execute("DELETE FROM entry_tags WHERE entry_id = %s", (entry_id,))
                    if tags:
                        for tag in tags:
                            cur.execute(
                                "INSERT INTO tags (user_id, name) VALUES (%s, %s) ON CONFLICT (user_id, name) DO NOTHING",
                                (request.user["id"], tag),
                            )
                        cur.execute(
                            "SELECT id, name FROM tags WHERE user_id = %s AND name = ANY(%s)",
                            (request.user["id"], tags),
                        )
                        tag_rows = cur.fetchall()
                        for tag_row in tag_rows:
                            cur.execute(
                                "INSERT INTO entry_tags (entry_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                                (entry_id, tag_row["id"]),
                            )
                cur.execute(
                    "UPDATE entries SET sentiment = %s WHERE id = %s",
                    (sentiment, entry_id),
                )
                conn.commit()
            entry = attach_tags(conn, [entry])[0]
        return jsonify(entry)

    @app.route("/api/entries/<int:entry_id>", methods=["DELETE"])
    @auth_required
    def delete_entry(entry_id):
        """Delete a journal entry.
        ---
        parameters:
          - in: path
            name: entry_id
            type: integer
            required: true
        responses:
          200:
            description: Deleted
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM entries WHERE id = %s AND user_id = %s", (entry_id, request.user["id"]))
                deleted = cur.rowcount
                conn.commit()
        if not deleted:
            return jsonify({"error": "Entry not found"}), 404
        return jsonify({"deleted": True})

    @app.route("/api/entries/export")
    @auth_required
    def export_entries():
        """Export entries as CSV or TXT.
        ---
        parameters:
          - in: query
            name: format
            type: string
        responses:
          200:
            description: OK
        """
        fmt = (request.args.get("format") or "csv").lower()
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, title, text, sentiment, created_at, updated_at FROM entries WHERE user_id = %s ORDER BY created_at DESC",
                    (request.user["id"],),
                )
                entries = cur.fetchall()
            entries = attach_tags(conn, entries)
        if fmt == "txt":
            lines = []
            for entry in entries:
                title = entry["title"] or "Untitled"
                lines.append(f"# {title}")
                lines.append(entry["text"])
                lines.append("")
            body = "\n".join(lines).strip() + "\n"
            response = make_response(body)
            response.headers["Content-Type"] = "text/plain"
            response.headers["Content-Disposition"] = "attachment; filename=entries.txt"
            return response
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "text", "sentiment", "tags", "created_at", "updated_at"])
        for entry in entries:
            writer.writerow(
                [
                    entry["id"],
                    entry["title"],
                    entry["text"],
                    entry["sentiment"],
                    ", ".join(entry.get("tags", [])),
                    entry["created_at"],
                    entry["updated_at"],
                ]
            )
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = "attachment; filename=entries.csv"
        return response

    @app.route("/api/tags", methods=["GET"])
    @auth_required
    def list_tags():
        """List tags with entry counts.
        ---
        responses:
          200:
            description: OK
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT t.name, COUNT(et.entry_id) AS count
                    FROM tags t
                    LEFT JOIN entry_tags et ON t.id = et.tag_id
                    WHERE t.user_id = %s
                    GROUP BY t.name
                    ORDER BY t.name
                    """,
                    (request.user["id"],),
                )
                tags = cur.fetchall()
        return jsonify(tags)

    @app.route("/api/uploads", methods=["POST"])
    @auth_required
    def upload_image():
        """Upload an image for inline markdown usage."""
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        file = request.files["image"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400
        raw = file.read()
        kind = imghdr.what(None, raw)
        if kind not in ALLOWED_IMAGE_TYPES:
            return jsonify({"error": "Unsupported image type"}), 400
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({"error": "Invalid filename"}), 400
        name, ext = os.path.splitext(filename)
        if not ext:
            ext = f".{kind}"
        safe_name = f"{name}-{int(time.time())}{ext}"
        upload_dir = ensure_upload_dir()
        file_path = os.path.join(upload_dir, safe_name)
        with open(file_path, "wb") as output:
            output.write(raw)
        url = f"/uploads/{safe_name}"
        return jsonify({"url": url})

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(UPLOAD_DIR, filename)

    @app.route("/api/dashboard/summary")
    @auth_required
    def dashboard_summary():
        """Get a summary of journaling stats.
        ---
        responses:
          200:
            description: OK
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) AS total FROM entries WHERE user_id = %s", (request.user["id"],))
                total_entries = cur.fetchone()["total"]
                cur.execute("SELECT COUNT(*) AS total FROM tags WHERE user_id = %s", (request.user["id"],))
                total_tags = cur.fetchone()["total"]
                cur.execute(
                    """
                    SELECT sentiment, COUNT(*) AS count
                    FROM entries
                    WHERE user_id = %s
                    GROUP BY sentiment
                    """,
                    (request.user["id"],),
                )
                sentiment_rows = cur.fetchall()
                cur.execute(
                    """
                    SELECT DATE(created_at) AS day, COUNT(*) AS count
                    FROM entries
                    WHERE user_id = %s AND created_at >= NOW() - INTERVAL '6 days'
                    GROUP BY day
                    ORDER BY day
                    """,
                    (request.user["id"],),
                )
                rows = cur.fetchall()
        counts = {row["day"]: row["count"] for row in rows}
        today = date.today()
        last_week = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            last_week.append({"day": day.isoformat(), "count": counts.get(day, 0)})
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for row in sentiment_rows:
            if row["sentiment"] in sentiment_counts:
                sentiment_counts[row["sentiment"]] = row["count"]
        return jsonify(
            {
                "total_entries": total_entries,
                "total_tags": total_tags,
                "sentiment_counts": sentiment_counts,
                "last_week": last_week,
            }
        )
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
