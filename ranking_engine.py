import requests
import numpy as np
import torch
import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from concurrent.futures import ThreadPoolExecutor, as_completed
import torch.nn.functional as F
from cache import get_cache, set_cache

load_dotenv()

API_KEY = os.environ.get("API_KEY")
MODEL_PATH = "lavishdabur/youtube-sentiment-model"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


tokenizer = None
model = None

def load_model():
    global tokenizer, model
    if model is None:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, cache_dir="./model_cache")
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, cache_dir="./model_cache")
        model.to(device)
        model.eval()


def normalize(values):
    min_v = min(values)
    max_v = max(values)

    if max_v == min_v:
        return [0.5 for _ in values]

    return [(v - min_v) / (max_v - min_v + 1e-6) for v in values]


def predict_sentiment(comments):
    load_model()

    inputs = tokenizer(
        comments,
        padding=True,
        truncation=True,
        max_length=128,   # reduced for speed
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    probs = F.softmax(outputs.logits, dim=1)
    return probs[:, 1].cpu().numpy()   # probability of positive


def search_videos(query, max_results=5):
    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print("Search API Error:", e)
        return []

    data = response.json()

    return [
        {
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"]
        }
        for item in data.get("items", [])
    ]


def get_comments_with_stats(video_id, max_results=15):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"

    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": max_results,
        "textFormat": "plainText",
        "order": "relevance",
        "key": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
    except Exception:
        return []

    data = response.json()

    comments = []
    for item in data.get("items", []):
        snippet = item["snippet"]["topLevelComment"]["snippet"]

        comments.append({
            "text": snippet["textDisplay"],
            "likes": snippet["likeCount"],
            "replies": item["snippet"]["totalReplyCount"]
        })

    return comments



def get_videos_metadata(video_ids):
    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
    except Exception:
        return {}

    data = response.json()

    ratios = {}
    for item in data.get("items", []):
        stats = item["statistics"]

        views = int(stats.get("viewCount", 1))
        likes = int(stats.get("likeCount", 0))

        ratios[item["id"]] = likes / views if views else 0

    return ratios



def compute_engagement_score(comment_data):
    total_comments = len(comment_data)

    if total_comments == 0:
        return 0

    total_likes = sum(c["likes"] for c in comment_data)
    total_replies = sum(c["replies"] for c in comment_data)

    avg_likes = total_likes / total_comments
    avg_replies = total_replies / total_comments

    return np.log1p(0.6 * avg_likes + 0.4 * avg_replies)



def process_video(v, metadata_ratios):
    video_id = v["video_id"]

    # Skip poor-quality videos early
    if metadata_ratios.get(video_id, 0) < 0.001:
        return None

    try:
        comment_data = get_comments_with_stats(video_id)

        if len(comment_data) == 0:
            sentiment_score = 0.5
            engagement_score = 0
        else:
            comments_text = [c["text"] for c in comment_data[:10]]

            sentiment_scores = predict_sentiment(comments_text)

            weights = [
                1 + np.log1p(c["likes"] + c["replies"])
                for c in comment_data[:10]
            ]

            sentiment_score = float(np.average(sentiment_scores, weights=weights))
            engagement_score = compute_engagement_score(comment_data)

        return {
            "title": v["title"],
            "video_id": video_id,
            "sentiment": sentiment_score,
            "engagement": engagement_score,
            "like_ratio": metadata_ratios.get(video_id, 0)
        }

    except Exception as e:
        print(f"Error processing video {video_id}: {e}")
        return None



def rank_videos_hybrid(query):

    query = query.lower().strip()

    cached = get_cache(query)
    if cached:
        print("Cache hit 🚀")
        return cached

    videos = search_videos(query, max_results=5)
    if not videos:
        return []

    video_ids = [v["video_id"] for v in videos]
    metadata_ratios = get_videos_metadata(video_ids)

    temp_results = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(process_video, v, metadata_ratios)
            for v in videos
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                temp_results.append(result)

    if not temp_results:
        return []

    engagement_values = [r["engagement"] for r in temp_results]
    like_ratio_values = [r["like_ratio"] for r in temp_results]

    norm_engagement = normalize(engagement_values)
    norm_like_ratio = normalize(like_ratio_values)

    results = []

    for i, r in enumerate(temp_results):

        final_score = (
            0.55 * r["sentiment"] +
            0.30 * norm_engagement[i] +
            0.15 * norm_like_ratio[i]
        )

        results.append({
            "title": r["title"],
            "video_id": r["video_id"],
            "score": round(final_score, 3),
            "sentiment": round(r["sentiment"], 3),
            "engagement": round(norm_engagement[i], 3),
            "like_ratio": round(norm_like_ratio[i], 3)
        })

    ranked = sorted(results, key=lambda x: x["score"], reverse=True)

    set_cache(query, ranked)

    return ranked