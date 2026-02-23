from flask import Blueprint, request, jsonify
import requests
import os

bp = Blueprint("payments", __name__)

PAYMENT_URL = os.getenv("PAYMENT_URL", "http://payment-mock:8080")

@bp.post("/payments/process")
def process():
    mode = request.args.get("mode", "ok")
    delay = request.args.get("delayMs", "0")
    r = requests.post(f"{PAYMENT_URL}/pay?mode={mode}&delayMs={delay}", timeout=3)
    return (r.text, r.status_code, {"Content-Type": "application/json"})