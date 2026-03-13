from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/health")
def health():
    return "ok", 200

@app.get("/api/v1/items")
def get_items():
    app.logger.info("[API] solicitud procesada en /api/v1/items")
    return jsonify([
        {"id": 1, "name": "item-1"},
        {"id": 2, "name": "item-2"}
    ]), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)