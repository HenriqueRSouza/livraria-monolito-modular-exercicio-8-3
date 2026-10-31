# Imagem para Azure App Service (contêiner) ou Azure Container Apps.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    LIVRARIA_DADOS=/home/dados

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY livraria ./livraria
COPY cliente ./cliente

EXPOSE 8000
# 1 worker com várias threads: os arquivos TXT têm trava, mas a saga de pedidos usa trava em memória.
CMD gunicorn --bind=0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 120 app:app
