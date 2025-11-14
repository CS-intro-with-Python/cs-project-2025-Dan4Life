from flask import Flask, jsonify, request

def create_app():
    app = Flask(__name__)
    
    @app.route("/api/status")
    def status():
        """Returns a simple health check response."""
        return jsonify({"ok": True})

    return app