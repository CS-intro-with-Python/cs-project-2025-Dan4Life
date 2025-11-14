from flask import Flask, jsonify, request, send_from_directory
from flasgger import Swagger
import os

entries = []

entries = []

def create_app():
    app = Flask(__name__)

    app.config['SWAGGER'] = {
        'title': 'MindSpace API',
        'uiversion': 3
    }

    Swagger(app)

    @app.route("/api/status")
    def status():
        return jsonify({"ok": True})

    @app.route("/api/entries", methods=["POST"])
    def create_entry():
        data = request.json or {}
        text = data.get("text", "")
        entry = {"id": len(entries) + 1, "text": text}
        entries.append(entry)
        return jsonify(entry), 201

    @app.route("/api/entries", methods=["GET"])
    def list_entries():
        return jsonify(entries)

    return app