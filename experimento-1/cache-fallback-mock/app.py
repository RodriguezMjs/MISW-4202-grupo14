from flask import Flask, jsonify
import os
import time
import psycopg2
import redis

app = Flask(__name__)

VALKEY_HOST = os.getenv("VALKEY_HOST", "valkey")
VALKEY_PORT = int(os.getenv("VALKEY_PORT", "6379"))

DB_HOST = os.getenv("DB_HOST", "postgres-replica")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "travelhub")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres_pass")

r = redis.Redis(host=VALKEY_HOST, port=VALKEY_PORT, decode_responses=True)

def db_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

@app.get("/health")
def health():
    return "ok", 200

@app.get("/cache/items/<item_id>")
def get_item(item_id: str):
    key = f"item:{item_id}"
    start = time.time()

    cached = r.get(key)
    if cached:
        return jsonify({"source":"cache","itemId":item_id,"value":cached,"ms": int((time.time()-start)*1000)}), 200

    # fallback a replica
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM items WHERE id = %s", (item_id,))
            row = cur.fetchone()

    value = row[0] if row else None
    r.setex(key, 60, value if value else "NOT_FOUND")

    return jsonify({"source":"replica","itemId":item_id,"value": value,"ms": int((time.time()-start)*1000)}), 200