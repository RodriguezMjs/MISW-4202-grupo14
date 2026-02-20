from flask import Blueprint, request, jsonify
from sqlalchemy import text
from utils.db import get_engine
from rabbitmq.producer import ItemProducer
import logging

logger = logging.getLogger(__name__)
items_bp = Blueprint("items", __name__)
engine = get_engine()


@items_bp.route("/items", methods=["POST"])
def create_item():
    """Create a new item and publish event to RabbitMQ."""
    payload = request.get_json() or {}
    name = payload.get("name")
    if not name:
        return jsonify({"error": "'name' is required"}), 400

    with engine.begin() as conn:
        conn.execute(
            text("CREATE TABLE IF NOT EXISTS items (id SERIAL PRIMARY KEY, name TEXT)")
        )
        result = conn.execute(
            text("INSERT INTO items (name) VALUES (:name) RETURNING id"), {"name": name}
        )
        new_id = result.scalar_one()

    # Publicar evento a RabbitMQ (productor)
    producer = ItemProducer()
    if producer.connect():
        producer.publish("item_created", {"id": new_id, "name": name})
        producer.close()
        logger.info(f"[PRODUCER] Evento 'item_created' publicado: id={new_id}, name={name}")
    else:
        logger.warning(f"[PRODUCER] Advertencia: No se pudo conectar a RabbitMQ")

    return jsonify({"id": new_id, "name": name}), 201


@items_bp.route("/items", methods=["GET"])
def list_items():
    """List all items."""
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name FROM items ORDER BY id")).all()
        items = [{"id": r.id, "name": r.name} for r in rows]
    return jsonify(items), 200


@items_bp.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """Get a specific item by ID."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name FROM items WHERE id = :id"), {"id": item_id}
        ).first()
    if not row:
        return jsonify({"error": "Item not found"}), 404
    return jsonify({"id": row.id, "name": row.name}), 200
