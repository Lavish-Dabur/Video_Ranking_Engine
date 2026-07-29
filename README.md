---
title: YouTube Video Ranking
emoji: "▶️"
colorFrom: red
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# YouTube Video Ranking

A full-stack application that finds YouTube videos for a search query and ranks them using comment sentiment, engagement, and like-to-view ratio.

The backend is a FastAPI service. It calls the YouTube Data API, uses a Hugging Face transformer to score comment sentiment, and stores completed rankings in Redis. The `frontend/` directory contains a React + Vite interface for searching and displaying ranked videos.

## Features

- Searches YouTube videos through the YouTube Data API v3.
- Analyses up to ten comments per video with a Hugging Face sequence-classification model.
- Combines sentiment (55%), normalized engagement (30%), and like ratio (15%) into a final score.
- Processes video comment analysis concurrently.
- Caches completed query results in Redis for five minutes.
- Uses short Redis timeouts and a cache fallback, so a cache outage does not block a search for several minutes.
- Loads the model once on demand with a lock, preventing concurrent workers from initializing it multiple times.

## Architecture

```text
React frontend
     │ POST /rank
     ▼
FastAPI backend ──► Redis cache
     │ cache miss
     ▼
YouTube Data API ──► metadata + comments ──► Hugging Face sentiment model
     │
     ▼
Ranked video results
```

## Tech stack

- **Backend:** Python, FastAPI, Uvicorn
- **Machine learning:** PyTorch, Hugging Face Transformers
- **Data:** YouTube Data API v3, Redis
- **Frontend:** React, Vite, Axios, Tailwind CSS, Recharts
- **Deployment:** Docker

## Prerequisites

- Python 3.10+
- A YouTube Data API v3 key
- A Redis instance (for example, Upstash Redis)
- Node.js 18+ to run the frontend locally

## Environment variables

Create a `.env` file in the project root:

```env
API_KEY=your_youtube_data_api_key
REDIS_URL=https://your-redis-host
REDIS_TOKEN=your_redis_password
```

`REDIS_URL` should be the Redis hostname with an optional `https://` prefix. The client connects with TLS on port `6379`.

## Run the backend locally

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 7860
```

The API is available at `http://127.0.0.1:7860`. The first ranking request downloads and loads the sentiment model; later requests reuse it from memory, and later starts reuse `model_cache/` when it exists.

## API

### `POST /rank`

Request body:

```json
{
  "query": "best python projects"
}
```

Example response:

```json
{
  "success": true,
  "query": "best python projects",
  "count": 1,
  "results": [
    {
      "title": "Example video",
      "video_id": "abc123",
      "score": 0.824,
      "sentiment": 0.791,
      "engagement": 0.862,
      "like_ratio": 0.743
    }
  ]
}
```

Interactive API documentation is available at `/docs`.

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

The current API URL is defined in `frontend/src/App.jsx`. Change it to `http://127.0.0.1:7860/rank` for local backend development.

## Docker

Build and run the backend:

```bash
docker build -t youtube-ranking-api .
docker run --rm -p 7860:7860 --env-file .env youtube-ranking-api
```

The `.dockerignore` excludes local virtual environments, Git history, the separate frontend, and model caches to keep Docker build context small. The model is loaded on demand, so the container can pass platform health checks before model download or initialization.

## Performance notes

- Redis operations have two-second connection and socket timeouts. When Redis is unavailable, the API continues without caching.
- The YouTube API calls use five-second request timeouts.
- The model load is protected by a lock, preventing parallel video workers from downloading or initializing it more than once.
- Final search results are cached for five minutes.

## Project structure

```text
.
├── app.py                # FastAPI routes and startup model warm-up
├── ranking_engine.py     # YouTube retrieval, sentiment, and ranking logic
├── cache.py              # Redis cache operations
├── redis_client.py       # Redis client configuration
├── frontend/             # React + Vite client
├── Dockerfile
└── requirements.txt
```
"# test" 
Testing github actions