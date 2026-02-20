from sqlalchemy import create_engine, text
from config import DATABASE_URL

_engine = None


def get_engine():
    """Get or create SQLAlchemy engine (singleton)."""
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
    return _engine


def init_db(engine):
    """Initialize database schema (create tables if they don't exist)."""
    with engine.begin() as conn:
        conn.execute(
            text("CREATE TABLE IF NOT EXISTS items (id SERIAL PRIMARY KEY, name TEXT)")
        )
