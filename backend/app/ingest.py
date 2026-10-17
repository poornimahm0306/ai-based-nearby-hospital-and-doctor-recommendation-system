# Script to create DB schema, insert sample providers, compute embeddings, and index in Qdrant
from app import db, embeddings
from app.data import SAMPLE_PROVIDERS
from sqlalchemy import text
from app.db import engine
import time

def ingest():
    print("Initializing DB...")
    db.init_db()
    time.sleep(1)
    with engine.begin() as conn:
        # clear table for idempotence in dev
        conn.execute(text("DELETE FROM providers;"))
        for p in SAMPLE_PROVIDERS:
            conn.execute(
                text(
                    "INSERT INTO providers (name, type, specialty, address, latitude, longitude, rating, bio) "
                    "VALUES (:name, :type, :specialty, :address, :latitude, :longitude, :rating, :bio) RETURNING id"
                ),
                {
                    "name": p["name"],
                    "type": p["type"],
                    "specialty": p["specialty"],
                    "address": p["address"],
                    "latitude": p["latitude"],
                    "longitude": p["longitude"],
                    "rating": p["rating"],
                    "bio": p["bio"],
                }
            )
        print("Inserted sample providers.")

    # compute embeddings and index in Qdrant
    # create a vector for each provider and index by id (id will be sequential from 1)
    print("Indexing providers in Qdrant...")
    dim = 1536 if embeddings.OPENAI_KEY else 64
    embeddings.ensure_collection(dim=dim)

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name, specialty, bio FROM providers")).all()
        for row in rows:
            pid = row[0]
            text_to_embed = f"{row[1]} {row[2]} {row[3]}"
            vec = embeddings.create_embedding(text_to_embed)
            payload = {"name": row[1], "specialty": row[2]}
            embeddings.index_provider(provider_id=pid, vector=vec, payload=payload)

    print("Ingest complete.")

if __name__ == "__main__":
    ingest()
