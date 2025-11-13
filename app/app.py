from flask import Flask, jsonify, request
from flasgger import Swagger

def create_app():
    app = Flask(__name__)
    Swagger(app)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status":"ok"})

    @app.route("/api/journal", methods=["POST"])
    def create_entry():
        payload = request.json or {}
        text = payload.get("text","")
        sentiment = "neutral"
        return jsonify({"id":1,"text":text,"sentiment":sentiment}),201

    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)