FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Keep the model in the image, so startup does not download it and the first
# visitor does not pay the model-loading cost.
RUN python -c "from transformers import AutoModelForSequenceClassification, AutoTokenizer; model = 'lavishdabur/updated_ranking_model'; AutoTokenizer.from_pretrained(model, cache_dir='/app/model_cache'); AutoModelForSequenceClassification.from_pretrained(model, cache_dir='/app/model_cache')"
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
