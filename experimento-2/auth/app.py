import os
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "auth-service")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "travelhub-clients")
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "15"))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_payload(
    username: str,
    role: str,
    expires_in_minutes: int,
    permissions: list[str] | None = None
) -> dict:
    now = utc_now()
    exp = now + timedelta(minutes=expires_in_minutes)

    return {
        "sub": username,
        "role": role,
        "permissions": permissions or [],
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE
    }


def build_expired_payload(
    username: str,
    role: str,
    permissions: list[str] | None = None
) -> dict:
    now = utc_now()

    return {
        "sub": username,
        "role": role,
        "permissions": permissions or [],
        "iat": int((now - timedelta(minutes=20)).timestamp()),
        "exp": int((now - timedelta(minutes=5)).timestamp()),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE
    }


def sign_token(payload: dict) -> str:
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "auth",
        "issuer": JWT_ISSUER,
        "audience": JWT_AUDIENCE,
        "algorithm": JWT_ALGORITHM
    }), 200


@app.get("/auth/config")
def auth_config():
    return jsonify({
        "issuer": JWT_ISSUER,
        "audience": JWT_AUDIENCE,
        "algorithm": JWT_ALGORITHM,
        "default_exp_minutes": JWT_EXP_MINUTES,
        "supported_roles": ["admin", "operator", "viewer"]
    }), 200


@app.post("/auth/token")
def issue_token():
    """
    Genera un token válido.
    Body ejemplo:
    {
      "username": "team14",
      "role": "admin",
      "permissions": ["items:read", "items:write"],
      "expires_in_minutes": 15
    }
    """
    body = request.get_json(silent=True) or {}

    username = body.get("username", "test-user")
    role = body.get("role", "viewer")
    permissions = body.get("permissions", [])
    expires_in_minutes = int(body.get("expires_in_minutes", JWT_EXP_MINUTES))

    payload = build_payload(
        username=username,
        role=role,
        expires_in_minutes=expires_in_minutes,
        permissions=permissions
    )
    token = sign_token(payload)

    return jsonify({
        "type": "valid",
        "access_token": token,
        "token_type": "Bearer",
        "claims": payload
    }), 200


@app.post("/auth/token-expired")
def issue_expired_token():
    """
    Genera un token expirado.
    """
    body = request.get_json(silent=True) or {}

    username = body.get("username", "test-user")
    role = body.get("role", "viewer")
    permissions = body.get("permissions", [])

    payload = build_expired_payload(
        username=username,
        role=role,
        permissions=permissions
    )
    token = sign_token(payload)

    return jsonify({
        "type": "expired",
        "access_token": token,
        "token_type": "Bearer",
        "claims": payload
    }), 200


@app.post("/auth/token-role-insufficient")
def issue_role_insufficient_token():
    """
    Genera un token válido pero con rol insuficiente.
    """
    body = request.get_json(silent=True) or {}

    username = body.get("username", "test-user")
    permissions = body.get("permissions", ["items:read"])

    payload = build_payload(
        username=username,
        role="viewer",
        expires_in_minutes=JWT_EXP_MINUTES,
        permissions=permissions
    )
    token = sign_token(payload)

    return jsonify({
        "type": "role_insufficient",
        "access_token": token,
        "token_type": "Bearer",
        "claims": payload
    }), 200


@app.post("/auth/token-malformed")
def malformed_token():
    """
    Devuelve un token malformado para pruebas.
    """
    return jsonify({
        "type": "malformed",
        "access_token": "abc.def",
        "token_type": "Bearer"
    }), 200


@app.post("/auth/token-tampered")
def tampered_token():
    """
    Genera un token válido y luego altera su firma para producir un token adulterado.
    """
    body = request.get_json(silent=True) or {}

    username = body.get("username", "test-user")
    role = body.get("role", "admin")
    permissions = body.get("permissions", ["items:read", "items:write"])

    payload = build_payload(
        username=username,
        role=role,
        expires_in_minutes=JWT_EXP_MINUTES,
        permissions=permissions
    )
    valid_token = sign_token(payload)

    parts = valid_token.split(".")
    if len(parts) != 3:
        return jsonify({"error": "Unexpected JWT structure"}), 500

    tampered_signature = parts[2][:-1] + ("A" if parts[2][-1] != "A" else "B")
    tampered_token = f"{parts[0]}.{parts[1]}.{tampered_signature}"

    return jsonify({
        "type": "tampered",
        "access_token": tampered_token,
        "token_type": "Bearer",
        "based_on_claims": payload
    }), 200


@app.post("/auth/login")
def login():
    """
    Login simplificado para el experimento.
    No valida usuarios reales; asigna permisos por rol.
    """
    body = request.get_json(silent=True) or {}

    username = body.get("username")
    role = body.get("role", "viewer")

    if not username:
        return jsonify({"error": "username is required"}), 400

    role_permissions = {
        "admin": ["items:read", "items:write", "admin:all"],
        "operator": ["items:read", "items:write"],
        "viewer": ["items:read"]
    }

    if role not in role_permissions:
        return jsonify({"error": "unsupported role"}), 400

    payload = build_payload(
        username=username,
        role=role,
        expires_in_minutes=JWT_EXP_MINUTES,
        permissions=role_permissions[role]
    )
    token = sign_token(payload)

    return jsonify({
        "message": "Login successful",
        "access_token": token,
        "token_type": "Bearer",
        "claims": payload
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)