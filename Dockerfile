FROM python:3.10

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
# Hugging Face's free CPU Spaces do not have a CUDA runtime.  Installing the
# default PyPI torch package pulls several gigabytes of NVIDIA libraries.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.2.2+cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 7860
CMD ["python", "-u", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--log-level", "debug"]
