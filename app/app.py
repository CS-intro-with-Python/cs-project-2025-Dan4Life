from flask import Flask, jsonify, request

entries = []

def create_app():
    app = Flask(__name__)

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

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8080)