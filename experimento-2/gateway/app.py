import os
from functools import wraps

from flask import Flask, jsonify, request, Response
import requests
import jwt

app = Flask(__name__)

# -------------------------
# Configuración
# -------------------------
UPSTREAM_API_BASE = os.getenv("UPSTREAM_API_BASE", "http://api:5001")
UPSTREAM_TIMEOUT_SEC = float(os.getenv("UPSTREAM_TIMEOUT_SEC", "3"))

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "auth-service")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "travelhub-clients")


# -------------------------
# Helpers JWT
# -------------------------
def extract_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "").strip()

    if not auth_header.startswith("Bearer "):
        return None

    parts = auth_header.split(" ", 1)
    if len(parts) != 2:
        return None

    token = parts[1].strip()
    return token or None


def require_jwt(required_role: str | None = None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = extract_bearer_token()

            if not token:
                app.logger.warning("[JWT] missing or invalid Authorization header")
                return jsonify({
                    "error": "MISSING_OR_INVALID_AUTH_HEADER",
                    "message": "Authorization header must use Bearer token"
                }), 401

            try:
                payload = jwt.decode(
                    token,
                    JWT_SECRET,
                    algorithms=[JWT_ALGORITHM],
                    issuer=JWT_ISSUER,
                    audience=JWT_AUDIENCE
                )
                request.jwt_payload = payload

            except jwt.ExpiredSignatureError:
                app.logger.warning("[JWT] rejected: token expired")
                return jsonify({
                    "error": "TOKEN_EXPIRED",
                    "message": "JWT is expired"
                }), 401

            except jwt.InvalidAudienceError:
                app.logger.warning("[JWT] rejected: invalid audience")
                return jsonify({
                    "error": "INVALID_AUDIENCE",
                    "message": "JWT audience is invalid"
                }), 401

            except jwt.InvalidIssuerError:
                app.logger.warning("[JWT] rejected: invalid issuer")
                return jsonify({
                    "error": "INVALID_ISSUER",
                    "message": "JWT issuer is invalid"
                }), 401

            except jwt.InvalidSignatureError:
                app.logger.warning("[JWT] rejected: invalid signature")
                return jsonify({
                    "error": "INVALID_SIGNATURE",
                    "message": "JWT signature is invalid"
                }), 401

            except jwt.DecodeError:
                app.logger.warning("[JWT] rejected: malformed token")
                return jsonify({
                    "error": "MALFORMED_TOKEN",
                    "message": "JWT is malformed"
                }), 401

            except jwt.InvalidTokenError:
                app.logger.warning("[JWT] rejected: invalid token")
                return jsonify({
                    "error": "INVALID_TOKEN",
                    "message": "JWT is invalid"
                }), 401

            token_role = payload.get("role")
            if required_role and token_role != required_role:
                app.logger.warning(
                    f"[JWT] rejected: forbidden role={token_role}, required={required_role}"
                )
                return jsonify({
                    "error": "FORBIDDEN",
                    "message": "Token does not have the required role",
                    "required_role": required_role,
                    "actual_role": token_role
                }), 403

            app.logger.info(
                f"[JWT] accepted: sub={payload.get('sub')} role={payload.get('role')}"
            )
            return fn(*args, **kwargs)

        return wrapper
    return decorator


# -------------------------
# Helpers proxy
# -------------------------
def proxy_response(resp: requests.Response) -> Response:
    content_type = resp.headers.get("Content-Type", "application/json")
    excluded_headers = {"content-encoding", "content-length", "transfer-encoding", "connection"}

    headers = [
        (name, value)
        for name, value in resp.headers.items()
        if name.lower() not in excluded_headers
    ]

    return Response(resp.content, resp.status_code, headers=headers, content_type=content_type)


# -------------------------
# Endpoints
# -------------------------
@app.get("/health")
def health():
    return "ok", 200


@app.get("/jwt/config")
def jwt_config():
    return jsonify({
        "algorithm": JWT_ALGORITHM,
        "issuer": JWT_ISSUER,
        "audience": JWT_AUDIENCE,
        "upstream_api_base": UPSTREAM_API_BASE
    }), 200


@app.get("/api/items")
@require_jwt(required_role="admin")
def get_items():
    """
    Endpoint protegido en el gateway.
    Si el JWT es válido y tiene role=admin, reenvía a la API.
    """
    upstream_url = f"{UPSTREAM_API_BASE}/api/v1/items"

    try:
        response = requests.get(upstream_url, timeout=UPSTREAM_TIMEOUT_SEC)
        return proxy_response(response)

    except requests.Timeout:
        app.logger.error("[GATEWAY] upstream timeout")
        return jsonify({
            "error": "UPSTREAM_TIMEOUT",
            "message": f"Upstream timeout after {UPSTREAM_TIMEOUT_SEC}s"
        }), 504

    except requests.RequestException as e:
        app.logger.error(f"[GATEWAY] upstream error: {str(e)}")
        return jsonify({
            "error": "UPSTREAM_ERROR",
            "message": str(e)
        }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7001)