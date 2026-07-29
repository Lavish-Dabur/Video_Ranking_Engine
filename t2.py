import os

from transformers import AutoModelForSequenceClassification

from ranking_engine import MODEL_PATH

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH,
    local_files_only=True,
)

print("Model loaded successfully")