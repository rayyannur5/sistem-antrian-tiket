# service1/Dockerfile dan service2/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get -y install tesseract-ocr tesseract-ocr-ind libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
