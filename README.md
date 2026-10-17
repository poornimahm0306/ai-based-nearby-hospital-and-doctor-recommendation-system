# Nearby Hospital & Doctor Recommendation (Dockerized MVP)

This repository contains an end-to-end MVP for recommending nearby hospitals and doctors using geospatial and semantic search.

Stack:
- FastAPI backend
- PostgreSQL + PostGIS
- Qdrant vector DB
- OpenAI embeddings (optional)
- React frontend with Tailwind
- Docker Compose to run everything locally

Quick start
1. Clone the repo and open the project directory.
2. Create backend/.env from backend/.env.example and set OPENAI_API_KEY.
3. Build & run:
   docker compose up --build
4. Wait for services to be healthy. In another terminal, ingest sample data:
   docker compose exec api python -m app.ingest
   (or call POST http://localhost:8000/ingest)
5. Open frontend: http://localhost:3000
6. API docs: http://localhost:8000/docs

Notes
- This local setup is for development. For production you should secure OpenAI keys, enable HTTPS, and configure volumes/backups.
- To switch to another embeddings provider or a self-hosted model, update `app/embeddings.py`.
