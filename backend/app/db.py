# Minimal synchronous DB helper
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/providersdb")
engine = create_engine(DATABASE_URL, echo=False, future=True)

def init_db():
    with engine.begin() as conn:
        # enable PostGIS extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        # providers table with geography point
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS providers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            specialty TEXT,
            address TEXT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            rating DOUBLE PRECISION,
            bio TEXT
        );
        """))
        # index for faster spatial queries (we use geometry from lat/lon at query-time)
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_providers_latlon ON providers (latitude, longitude);"))
