import json
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

# Импортируем SentenceTransformer для создания эмбеддингов и util для математики
from sentence_transformers import SentenceTransformer, util

app = FastAPI(title="AIOps Log Analyzer API")

# ==========================================
# УРОВЕНЬ 1: Оперативный энкодер (Fast Encoder)
# ==========================================
print("Загрузка модели Sentence-BERT (all-MiniLM-L6-v2)...")
# Это та самая модель из статьи, она весит всего ~90 МБ и летает на процессоре
encoder = SentenceTransformer("all-MiniLM-L6-v2")

print("Инициализация векторов аномалий...")
# Создаем словарь разных якорей
ANCHORS = {
    "hardware_crash": "critical failure error exception anomaly crash hardware timeout",
    "security_auth": "unauthorized denied login failed authentication brute force attack breach",
    "database_sql": "sql injection syntax error deadlock database connection lost"
}

# Заранее кодируем их все в векторы
anchor_embeddings = {
    category: encoder.encode(text, convert_to_tensor=True)
    for category, text in ANCHORS.items()
}

class LogEntry(BaseModel):
    log_text: str


@app.post("/analyze")
async def analyze_log(entry: LogEntry):
    # 1. Превращаем пришедший лог в вектор
    log_emb = encoder.encode(entry.log_text, convert_to_tensor=True)

    # Считаем сходство со всеми якорями
    max_sim = 0.0
    for category, emb in anchor_embeddings.items():
        sim = util.cos_sim(log_emb, emb).item()
        if sim > max_sim:
            max_sim = sim

    # Если лог не похож НИ НА ОДНУ из аномалий (ни на железо, ни на взлом)
    if max_sim < 0.3:
        return {
            "status": "normal",
            "encoder_confidence": round(max_sim, 3),
            "message": "Отфильтровано (Аномалий нет)"
        }

    # ==========================================
    # УРОВЕНЬ 2: Генеративная LLM (Root Cause Analysis)
    # ==========================================
    ollama_url = "http://ollama:11434/api/generate"

    # ИСПРАВЛЕНИЕ: Добавили сам текст лога {entry.log_text} в промпт!
    prompt = f"""
    Ты AIOps-инженер. Проанализируй системный лог. 
    Верни ответ СТРОГО в формате JSON с двумя ключами:
    1. "status": "normal" (только рутинные логи, без ошибок и предупреждений) или "anomaly_detected" (ЛЮБЫЕ ошибки, сбои, warnings, аппаратные проблемы, даже если система их исправила или проигнорировала).
    2. "root_cause_analysis": "Краткое объяснение"
    ВАЖНО: штатные переподключения, рутинные таймауты ожидания и процессы сборки мусора (GC) считай нормальными). Пример нормального лога: "Connection retry 1 of 3" -> status: "normal".

    ЛОГ ДЛЯ АНАЛИЗА:
    {entry.log_text}
    """

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(ollama_url, json={
                "model": "qwen2.5",
                "prompt": prompt,
                "stream": False,
                "format": "json"  # <-- Подсказка для Ollama, чтобы она старалась отдавать чистый JSON
            }, timeout=60.0)

            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Ollama API Error: {response.text}"
                }

            ollama_data = response.json()
            qwen_response_text = ollama_data.get("response", "{}")

            # Очищаем строку
            qwen_response_text = qwen_response_text.strip().strip("`").removeprefix("json").strip()

            # Парсим JSON
            llm_result = json.loads(qwen_response_text)

        print(
            f"ЛОГ: {entry.log_text[:60]}... | СИМИЛЯРНОСТЬ: {max_sim:.3f} | ОТВЕТ LLM: {llm_result.get('status')}")

        return {
            "status": llm_result.get("status", "error"),
            "encoder_confidence": round(max_sim, 3),  # Передаем метрику подозрительности
            "root_cause_analysis": llm_result.get("root_cause_analysis", "Нет данных")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка связи с LLM или парсинга JSON: {str(e)}"
        }