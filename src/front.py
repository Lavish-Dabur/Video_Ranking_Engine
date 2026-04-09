import streamlit as st
from ranking_engine import rank_videos_hybrid

st.set_page_config(
    page_title="YouTube Quality Ranking System",
    layout="wide"
)

st.title("YouTube Comment-Based Video Quality Ranking")

st.write("""
This system ranks YouTube videos based on **audience opinion** using:

• Comment Sentiment (DistilBERT)  
• Engagement Score  
• Like/View Ratio  

Videos are ranked using a **hybrid scoring model**.
""")

query = st.text_input(" Enter YouTube Search Query")

if st.button("Rank Videos"):

    if query.strip() == "":
        st.warning("Please enter a search query")
    else:

        with st.spinner("Fetching videos and analyzing comments..."):

            results = rank_videos_hybrid(query)

        st.success("Ranking completed!")

        st.divider()

        st.subheader("📊 Ranked Results")

        for i, r in enumerate(results):

            col1, col2 = st.columns([1,3])

            with col1:

                st.write(f"### #{i+1}")

                st.write("**Score**")
                st.metric("Final Score", round(r["score"],3))

                st.write("**Score Breakdown**")

                st.write(f"Sentiment Score: {round(r['sentiment'],3)}")
                st.write(f"Engagement Score: {round(r['engagement'],3)}")
                st.write(f"Like Ratio: {round(r['like_ratio'],6)}")

            with col2:

                st.subheader(r["title"])

                video_url = f"https://www.youtube.com/watch?v={r['video_id']}"

                st.video(video_url)

                st.write("Watch on YouTube:")
                st.write(video_url)

            st.divider()