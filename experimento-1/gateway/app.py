import os
import time
import json
from flask import Flask, jsonify, request, Response
import requests
import pybreaker

app = Flask(__name__)

# -------------------------
# Config (env vars)
# -------------------------
UPSTREAM_API_BASE = os.getenv("UPSTREAM_API_BASE", "http://api:5000")
PAYMENT_BASE = os.getenv("PAYMENT_BASE", "http://payment-mock:8080")

# Timeout del request al upstream (corto para fail-fast)
UPSTREAM_TIMEOUT_SEC = float(os.getenv("UPSTREAM_TIMEOUT_SEC", "1.5"))

# Circuit breaker parameters
CB_FAIL_MAX = int(os.getenv("CB_FAIL_MAX", "5"))          # fallos para abrir
CB_RESET_TIMEOUT = int(os.getenv("CB_RESET_TIMEOUT", "15"))  # segundos abierto antes de half-open


# -------------------------
# Helpers: circuit breaker listeners (para logs evidenciables)
# -------------------------
class CBListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        app.logger.warning(f"[CB] state_change {old_state.name} -> {new_state.name}")

    def failure(self, cb, exc):
        app.logger.warning(f"[CB] failure: {type(exc).__name__}: {exc}")

    def success(self, cb):
        app.logger.info("[CB] success")


breaker_api = pybreaker.CircuitBreaker(
    fail_max=CB_FAIL_MAX,
    reset_timeout=CB_RESET_TIMEOUT,
    listeners=[CBListener()],
    name="api-breaker"
)

breaker_payment = pybreaker.CircuitBreaker(
    fail_max=CB_FAIL_MAX,
    reset_timeout=CB_RESET_TIMEOUT,
    listeners=[CBListener()],
    name="payment-breaker"
)


# -------------------------
# Routes
# -------------------------
@app.get("/health")
def health():
    return "ok", 200


@app.get("/cb/state")
def cb_state():
    return jsonify({
        "api_breaker": breaker_api.current_state.name,
        "payment_breaker": breaker_payment.current_state.name,
        "fail_max": CB_FAIL_MAX,
        "reset_timeout_sec": CB_RESET_TIMEOUT
    }), 200


def _proxy_json(resp: requests.Response) -> Response:
    # Preserva status y body del upstream
    content_type = resp.headers.get("Content-Type", "application/json")
    return Response(resp.content, status=resp.status_code, content_type=content_type)


@app.get("/api/items")
def proxy_items():
    """
    Proxy protegido por circuit breaker hacia UPSTREAM_API_BASE + /api/items o /items, según tu API.
    Ajusta la URL abajo si tu API no tiene /api.
    """

    upstream_url = f"{UPSTREAM_API_BASE}/api/items"

    try:
        # breaker_api.call ejecuta la función o lanza CircuitBreakerError si OPEN
        def _call():
            return requests.get(upstream_url, timeout=UPSTREAM_TIMEOUT_SEC)

        resp = breaker_api.call(_call)
        return _proxy_json(resp)

    except pybreaker.CircuitBreakerError:
        # Circuito OPEN: respuesta inmediata (fail-fast), sin tocar upstream
        return jsonify({
            "error": "UPSTREAM_UNAVAILABLE",
            "breaker": "OPEN",
            "message": "Circuit breaker is open. Failing fast."
        }), 503

    except requests.Timeout:
        # Timeout cuenta como fallo -> breaker suma
        return jsonify({
            "error": "UPSTREAM_TIMEOUT",
            "breaker": breaker_api.current_state.name,
            "message": f"Upstream timeout after {UPSTREAM_TIMEOUT_SEC}s"
        }), 504

    except requests.RequestException as e:
        return jsonify({
            "error": "UPSTREAM_ERROR",
            "breaker": breaker_api.current_state.name,
            "message": str(e)
        }), 502


@app.post("/api/payments/process")
def proxy_payment():
    """
    Proxy protegido por circuit breaker hacia payment mock:
    POST {PAYMENT_BASE}/pay?mode=ok|error|slow&delayMs=...
    """

    mode = request.args.get("mode", "ok")
    delay_ms = request.args.get("delayMs", "0")
    upstream_url = f"{PAYMENT_BASE}/pay?mode={mode}&delayMs={delay_ms}"

    try:
        def _call():
            return requests.post(upstream_url, timeout=UPSTREAM_TIMEOUT_SEC)

        resp = breaker_payment.call(_call)
        return _proxy_json(resp)

    except pybreaker.CircuitBreakerError:
        return jsonify({
            "error": "PAYMENT_UNAVAILABLE",
            "breaker": "OPEN",
            "message": "Payment circuit breaker is open. Failing fast."
        }), 503

    except requests.Timeout:
        return jsonify({
            "error": "PAYMENT_TIMEOUT",
            "breaker": breaker_payment.current_state.name,
            "message": f"Payment timeout after {UPSTREAM_TIMEOUT_SEC}s"
        }), 504

    except requests.RequestException as e:
        return jsonify({
            "error": "PAYMENT_ERROR",
            "breaker": breaker_payment.current_state.name,
            "message": str(e)
        }), 502