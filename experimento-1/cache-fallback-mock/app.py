"""
cache-fallback-mock
-------------------
Mock que demuestra la táctica de cache fallback del experimento.

Flujo:
  1. GET /hotels → busca en Valkey primero (cache hit → responde sin tocar BD)
  2. Si no hay cache → consulta PostgreSQL Replica y guarda en Valkey (cache miss)
  3. Si PostgreSQL está caído → responde desde cache igual (cache fallback)

Endpoints:
  GET  /hotels          → lista hoteles (con cache)
  GET  /hotels/nocache  → lista hoteles forzando consulta a BD (para comparar)
  POST /cache/clear     → limpia el cache (para resetear el experimento)
  GET  /health          → estado del servicio, BD y cache
"""

import os
import json
import time
import psycopg2
import redis
from flask import Flask, jsonify

app = Flask(__name__)

# ── Configuración ──────────────────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST", "postgres-replica")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "travelhub")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres_pass")

VALKEY_HOST = os.getenv("VALKEY_HOST", "valkey")
VALKEY_PORT = int(os.getenv("VALKEY_PORT", "6379"))
CACHE_TTL   = int(os.getenv("CACHE_TTL", "30"))   # segundos que vive el cache

CACHE_KEY   = "hotels:all"

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_cache_client():
    return redis.Redis(host=VALKEY_HOST, port=VALKEY_PORT, decode_responses=True)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        connect_timeout=3
    )

def query_hotels_from_db():
    """Consulta hoteles directamente desde PostgreSQL Replica."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, city, available_rooms FROM hotels ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "city": r[2], "available_rooms": r[3]}
        for r in rows
    ]

# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.route("/hotels", methods=["GET"])
def get_hotels():
    """
    Endpoint principal — demuestra el patrón cache-aside:
      - Cache hit:      responde desde Valkey (fuente: cache)
      - Cache miss:     va a PostgreSQL, guarda en cache (fuente: database)
      - BD caída:       responde desde cache aunque PostgreSQL no esté (fuente: cache_fallback)
    """
    cache = get_cache_client()
    start = time.time()

    # 1. Intentar cache primero
    try:
        cached = cache.get(CACHE_KEY)
        if cached:
            return jsonify({
                "source": "cache",
                "ttl_remaining_seconds": cache.ttl(CACHE_KEY),
                "response_ms": round((time.time() - start) * 1000, 2),
                "hotels": json.loads(cached)
            })
    except Exception as e:
        # Valkey no disponible — intentamos BD directamente
        pass

    # 2. Cache miss → consultar PostgreSQL
    try:
        hotels = query_hotels_from_db()
        # Guardar en cache para próximas requests
        try:
            cache.setex(CACHE_KEY, CACHE_TTL, json.dumps(hotels))
        except Exception:
            pass  # Si Valkey falla al guardar, igual respondemos
        return jsonify({
            "source": "database",
            "cache_ttl_seconds": CACHE_TTL,
            "response_ms": round((time.time() - start) * 1000, 2),
            "hotels": hotels
        })
    except Exception as db_error:
        # 3. BD caída → intentar cache como fallback
        try:
            cached = cache.get(CACHE_KEY)
            if cached:
                return jsonify({
                    "source": "cache_fallback",
                    "warning": "PostgreSQL no disponible, sirviendo desde cache",
                    "response_ms": round((time.time() - start) * 1000, 2),
                    "hotels": json.loads(cached)
                })
        except Exception:
            pass

        # Sin cache ni BD → error controlado
        return jsonify({
            "source": "none",
            "error": "PostgreSQL no disponible y no hay cache",
            "detail": str(db_error)
        }), 503


@app.route("/hotels/nocache", methods=["GET"])
def get_hotels_no_cache():
    """
    Fuerza consulta directa a PostgreSQL sin usar cache.
    Útil para comparar tiempos de respuesta con /hotels.
    """
    start = time.time()
    try:
        hotels = query_hotels_from_db()
        return jsonify({
            "source": "database_direct",
            "response_ms": round((time.time() - start) * 1000, 2),
            "hotels": hotels
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route("/cache/clear", methods=["POST"])
def clear_cache():
    """Limpia el cache — útil para resetear entre escenarios del experimento."""
    try:
        cache = get_cache_client()
        cache.delete(CACHE_KEY)
        return jsonify({"message": "Cache limpiado", "key": CACHE_KEY})
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route("/health", methods=["GET"])
def health():
    """Estado del servicio, PostgreSQL y Valkey — usado por Nginx para health checks."""
    status = {"service": "ok", "database": "unknown", "cache": "unknown"}

    try:
        conn = get_db_connection()
        conn.close()
        status["database"] = "ok"
    except Exception as e:
        status["database"] = f"error: {str(e)}"

    try:
        cache = get_cache_client()
        cache.ping()
        status["cache"] = "ok"
    except Exception as e:
        status["cache"] = f"error: {str(e)}"

    http_status = 200 if status["database"] == "ok" else 207
    return jsonify(status), http_status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
