from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import time
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

def init_db(engine, retries: int = 30, delay_sec: float = 2.0) -> None:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError as e:
            last_err = e
            print(f"[DB] not ready (attempt {attempt}/{retries}), retry in {delay_sec}s: {e}")
            time.sleep(delay_sec)

    raise RuntimeError("DB never became ready") from last_err

def get_engine() -> Engine:
    host = os.getenv("DB_HOST", "postgres-primary")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "travelhub")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres_pass")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    return create_engine(url, pool_pre_ping=True)