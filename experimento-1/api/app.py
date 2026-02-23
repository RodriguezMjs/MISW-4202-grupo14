from flask import Flask
from config import DATABASE_URL
from utils.db import init_db, get_engine
from blueprints.items import items_bp
from blueprints.health import health_bp
import time

app = Flask(__name__)


# Register Blueprints
app.register_blueprint(health_bp, url_prefix="/api/v1")
app.register_blueprint(items_bp, url_prefix="/api/v1")


@app.before_first_request
def ensure_db_initialized():
    """Try to initialize DB schema with retries to tolerate DB/pgpool startup.

    This avoids failing Gunicorn workers at import time when the DB proxy
    (`pgpool`) is not yet accepting connections.
    """
    engine = get_engine()
    retries = 10
    delay = 2
    for attempt in range(1, retries + 1):
        try:
            init_db(engine)
            app.logger.info("Database initialized")
            return
        except Exception as e:
            app.logger.warning(
                f"Database init attempt {attempt}/{retries} failed: {e}"
            )
            time.sleep(delay)
    app.logger.error("Database initialization failed after retries")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
