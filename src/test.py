from ranking_engine import rank_videos_hybrid

query = "Data Structures Tutorial"

print("Running ranking engine...\n")

results = rank_videos_hybrid(query)

print("Results:\n")

for i, r in enumerate(results):

    print(f"{i+1}. {r['title']}")
    print("Video ID:", r["video_id"])
    print("Score:", round(r["score"],3))
    print("Sentiment:", round(r["sentiment"],3))
    print("Engagement:", round(r["engagement"],3))
    print("Like Ratio:", round(r["like_ratio"],6))
    print("-"*50)