# Wrapper around OpenAI embeddings and Qdrant indexing
import os
import openai
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
qclient = QdrantClient(url=QDRANT_URL)

COLLECTION = "providers"

def create_embedding(text: str) -> list:
    if not OPENAI_KEY:
        # Fallback: small deterministic bag-of-words-ish vector — not production-grade.
        tokens = [w for w in text.lower().split()][:64]
        vec = [float(len(w)) for w in tokens]
        # pad/truncate to 64
        vec = (vec + [0.0]*64)[:64]
        return vec
    res = openai.Embedding.create(model="text-embedding-3-small", input=text)
    return res["data"][0]["embedding"]

def ensure_collection(dim: int):
    try:
        qclient.get_collection(COLLECTION)
    except Exception:
        qclient.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE),
        )

def index_provider(provider_id: int, vector: list, payload: dict = None):
    qclient.upsert(
        collection_name=COLLECTION,
        points=[
            rest.PointStruct(id=provider_id, vector=vector, payload=payload or {})
        ],
    )

def search_vectors(query_vector: list, top_k: int = 10, filter_payload: dict = None):
    # filter_payload can be used to restrict by provider attributes in Qdrant payload
    res = qclient.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
        # filter=None
    )
    return res
