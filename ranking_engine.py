import requests
import numpy as np
import torch
import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

API_KEY = os.environ.get("API_KEY")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = "lavishdabur/youtube-sentiment-model"

print("Loading model from:", MODEL_PATH)
print("Model exists:", os.path.exists(MODEL_PATH))

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(device)

try:
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH,
        cache_dir="./model_cache"
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_PATH,
        cache_dir="./model_cache"
    )

    model.to(device)
    model.eval()

    print("Model loaded successfully")

except Exception as e:
    print("Error loading model:", e)


def normalize(values):

    min_v = min(values)
    max_v = max(values)

    if max_v == min_v:
        return [0.5 for _ in values]

    return [(v - min_v) / (max_v - min_v) for v in values]



def predict_sentiment(comments):

    inputs = tokenizer(
        comments,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    predictions = torch.argmax(outputs.logits, dim=1).numpy()

    return predictions




def compute_sentiment_score(predictions):

    total = len(predictions)

    positive = np.sum(predictions == 1)
    negative = np.sum(predictions == 0)

    Sp = positive / total
    Sn = negative / total

    sentiment_score = (Sp - Sn + 1) / 2

    return Sp, Sn, sentiment_score




def search_videos(query, max_results=5):

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": API_KEY
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        print("API Error:", response.text)
        return []

    data = response.json() if response.content else {}

    videos = []

    for item in data.get("items", []):

        videos.append({
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"]
        })

    return videos



def get_comments_with_stats(video_id, max_results=50):

    comments = []

    url = "https://www.googleapis.com/youtube/v3/commentThreads"

    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": max_results,
        "textFormat": "plainText",
        "order": "relevance",
        "key": API_KEY
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        print("API Error:", response.text)
        return []

    data = response.json() if response.content else {}

    for item in data.get("items", []):

        snippet = item["snippet"]["topLevelComment"]["snippet"]

        comments.append({
            "text": snippet["textDisplay"],
            "likes": snippet["likeCount"],
            "replies": item["snippet"]["totalReplyCount"]
        })

    return comments



def compute_engagement_score(comment_data):

    total_comments = len(comment_data)

    total_likes = sum(c["likes"] for c in comment_data)
    total_replies = sum(c["replies"] for c in comment_data)

    avg_likes = total_likes / total_comments if total_comments else 0
    avg_replies = total_replies / total_comments if total_comments else 0

    engagement_score = (0.6 * avg_likes) + (0.4 * avg_replies)

    return np.log1p(engagement_score)



def get_videos_metadata(video_ids):

    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": API_KEY
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        print("API Error:", response.text)
        return []

    data = response.json() if response.content else {}

    ratios = {}

    for item in data.get("items", []):

        stats = item["statistics"]

        views = int(stats.get("viewCount", 1))
        likes = int(stats.get("likeCount", 0))

        ratio = likes / views if views else 0

        ratios[item["id"]] = ratio

    return ratios



def process_video(v, metadata_ratios):

    video_id = v["video_id"]

    try:
        comment_data = get_comments_with_stats(video_id, max_results=50)

        if len(comment_data) == 0:
            return None

        comments_text = [c["text"] for c in comment_data]

        predictions = predict_sentiment(comments_text)

        Sp, Sn, sentiment_score = compute_sentiment_score(predictions)

        sentiment_score = (sentiment_score + 1) / 2

        engagement_score = compute_engagement_score(comment_data)

        like_ratio = metadata_ratios.get(video_id, 0)

        return {
            "title": v["title"],
            "video_id": video_id,
            "sentiment": sentiment_score,
            "engagement": engagement_score,
            "like_ratio": like_ratio
        }

    except Exception as e:
        print(f"Error processing video {video_id}: {e}")
        return None



def rank_videos_hybrid(query):

    videos = search_videos(query, max_results=5)

    if len(videos) == 0:
        return []

    video_ids = [v["video_id"] for v in videos]
    metadata_ratios = get_videos_metadata(video_ids)

    temp_results = []

    temp_results = []

    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = [
            executor.submit(process_video, v, metadata_ratios)
            for v in videos
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                temp_results.append(result)

    if len(temp_results) == 0:
        return []

    engagement_values = [r["engagement"] for r in temp_results]
    like_ratio_values = [r["like_ratio"] for r in temp_results]

    norm_engagement = normalize(engagement_values)
    norm_like_ratio = normalize(like_ratio_values)

    results = []

    for i, r in enumerate(temp_results):

        final_score = (
            0.5 * r["sentiment"] +
            0.3 * norm_engagement[i] +
            0.2 * norm_like_ratio[i]
        )

        results.append({
            "title": r["title"],
            "video_id": r["video_id"],
            "score": final_score,
            "sentiment": r["sentiment"],
            "engagement": norm_engagement[i],
            "like_ratio": norm_like_ratio[i]
        })

    ranked = sorted(results, key=lambda x: x["score"], reverse=True)

    return ranked



if __name__ == "__main__":

    print("Testing YouTube Ranking Engine...\n")

    query = "data structures tutorial"

    results = rank_videos_hybrid(query)

    print("\nRanked Results:\n")

    for i, r in enumerate(results):

        print(f"{i+1}. {r['title']}")
        print("Video ID:", r["video_id"])
        print("Score:", round(r["score"],3))
        print("Sentiment:", round(r["sentiment"],3))
        print("Engagement:", round(r["engagement"],3))
        print("Like Ratio:", round(r["like_ratio"],6))
        print("-"*60)