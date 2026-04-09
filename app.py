import asyncio

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from ranking_engine import rank_videos_hybrid

app = FastAPI(
    title="YouTube Ranking API",
    description="Ranks YouTube videos using sentiment + engagement",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


@app.get("/")
def home():
    return {"status": "API is running 🚀"}



@app.post("/rank")
async def rank_videos(request: QueryRequest):

    try:
        results = await asyncio.to_thread(rank_videos_hybrid, request.query)

        return {
            "success": True,
            "query": request.query,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }