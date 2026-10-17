# FastAPI: recommend endpoint combining PostGIS distance + Qdrant semantic similarity
import os, math
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.db import engine, init_db
from sqlalchemy import text
from app import embeddings

app = FastAPI(title="Nearby Hospital & Doctor Recommendation API")

# health
@app.get("/health")
def health():
    return {"status": "ok"}

class RecommendRequest(BaseModel):
    latitude: float
    longitude: float
    query: Optional[str] = ""
    specialty: Optional[str] = None
    max_distance_km: float = 20.0
    limit: int = 5

def haversine_km(lat1, lon1, lat2, lon2):
    R=6371.0
    phi1=math.radians(lat1); phi2=math.radians(lat2)
    dphi=math.radians(lat2-lat1); dlambda=math.radians(lon2-lon1)
    a=(math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2)
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.post("/ingest")
def ingest_endpoint():
    # convenience endpoint to run ingest inside container
    try:
        from app.ingest import ingest
        ingest()
        return {"status": "ingest_started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend")
def recommend(req: RecommendRequest):
    # 1) run PostGIS-style radius search (we store lat/lon; use ST_DWithin with geography)
    radius_m = req.max_distance_km * 1000.0
    q = text("""
        SELECT id, name, type, specialty, address, latitude, longitude, rating, bio
        FROM providers
        WHERE ST_DWithin(
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
            :radius_m
        );
    """)
    rows = []
    with engine.connect() as conn:
        # Ensure DB exists and tables are created
        init_db()
        res = conn.execute(q, {"lon": req.longitude, "lat": req.latitude, "radius_m": radius_m})
        rows = res.fetchall()

    if not rows:
        return {"recommendations": []}

    # Build candidate list
    candidates = []
    for r in rows:
        pid, name, ptype, specialty, address, lat, lon, rating, bio = r
        dist = haversine_km(req.latitude, req.longitude, lat, lon)
        candidates.append({
            "id": pid, "name": name, "type": ptype, "specialty": specialty,
            "address": address, "latitude": lat, "longitude": lon,
            "rating": rating, "bio": bio, "distance_km": round(dist,2)
        })

    # 2) optional semantic ranking: if query provided, use OpenAI embeddings + Qdrant
    semantic_scores = {}
    if req.query:
        qvec = embeddings.create_embedding(req.query)
        results = embeddings.search_vectors(qvec, top_k=50)
        # results are list of PointStruct with id, score, payload
        for r in results:
            # Qdrant returns id as int (matching provider id)
            pid = int(r.id)
            semantic_scores[pid] = r.score  # cosine similarity-ish (closer is better)

    # 3) combine scores
    ranked = []
    # normalize distance with a simple decay
    max_dist = max([c["distance_km"] for c in candidates] + [req.max_distance_km])
    for c in candidates:
        distance_score = max(0.0, 1.0 - (c["distance_km"] / max_dist))
        semantic = semantic_scores.get(c["id"], None)
        semantic_score = float(semantic) if semantic is not None else 0.0
        # normalize semantic between 0..1 assuming Qdrant score is [0..1] (cosine). If >1 adjust later.
        # combine weights
        final = 0.55 * distance_score + 0.35 * semantic_score + 0.10 * (c["rating"] / 5.0)
        if req.specialty and req.specialty.lower() in (c["specialty"] or "").lower():
            final = final + 0.1  # small boost
        ranked.append({
            **c,
            "distance_score": round(distance_score,4),
            "semantic_score": round(semantic_score,4),
            "match_score": round(final,4)
        })

    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return {"recommendations": ranked[: req.limit]}
