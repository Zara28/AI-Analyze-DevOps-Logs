FROM python:3.10-slim

WORKDIR /app

# Копируем список зависимостей
COPY requirements.txt .

# Устанавливаем библиотеки (torch может качаться довольно долго)
RUN pip install --no-cache-dir -r requirements.txt

# Предзагружаем веса легковесной модели DistilBERT при сборке образа
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='typeform/distilbert-base-uncased-mnli')"

# Копируем основной код
COPY main.py .

# Запускаем FastAPI на 8000 порту
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]