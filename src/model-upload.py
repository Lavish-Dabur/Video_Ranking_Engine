from huggingface_hub import HfApi

from ranking_engine import MODEL_PATH

api = HfApi()

api.upload_folder(
    folder_path=MODEL_PATH,
    repo_id="lavishdabur/youtube-sentiment-model",
    repo_type="model"
)