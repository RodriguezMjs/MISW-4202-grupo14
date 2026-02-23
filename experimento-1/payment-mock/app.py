from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.get("/health")
def health():
    return "ok", 200

@app.post("/pay")
def pay():
    mode = request.args.get("mode", "ok")
    delay_ms = int(request.args.get("delayMs", "0"))

    if mode == "slow":
        time.sleep(delay_ms / 1000.0)
        return jsonify({"status": "APPROVED", "mode": "slow", "delayMs": delay_ms}), 200

    if mode == "error":
        return jsonify({"status": "DECLINED", "mode": "error"}), 502

    return jsonify({"status": "APPROVED", "mode": "ok"}), 200