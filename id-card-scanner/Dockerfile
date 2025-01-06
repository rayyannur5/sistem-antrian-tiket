# Base image
FROM python:3.9-slim


WORKDIR /app


COPY requirements.txt /app/

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-ind \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt


COPY . /app/

# Perintah default untuk container
CMD ["python", "app.py"]
