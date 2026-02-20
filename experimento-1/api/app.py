from flask import Flask
from config import DATABASE_URL
from utils.db import init_db, get_engine
from blueprints.items import items_bp
from blueprints.health import health_bp

app = Flask(__name__)

# Initialize DB schema at startup
engine = get_engine()
init_db(engine)

# Register Blueprints
app.register_blueprint(health_bp, url_prefix="/api/v1")
app.register_blueprint(items_bp, url_prefix="/api/v1")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
