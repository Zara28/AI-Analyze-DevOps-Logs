import requests
import time

# Твой URL вебхука из n8n (Production URL или Test URL)
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/5e8dea2f-fcac-48cd-b140-139f9b5d5894"

dataset = [
    # Нормальные логи 
    {"log": "081109 203518 143 INFO dfs.DataNode: Receiving block blk_-160899", "actual_label": "normal"},
    {"log": "INFO: User login successful for account id 8834", "actual_label": "normal"},
    {"log": "1117838570 INFO instruction cache parity error corrected", "actual_label": "normal"},
    
    # Аномальные логи
    {"log": "081109 204655 346 WARN dfs.DataNode: Got exception while serving blk_-354458", "actual_label": "anomaly"},
    {"log": "FATAL data TLB error interrupt in memory module", "actual_label": "anomaly"},
    {"log": "ERROR: Database connection timed out after 30000ms", "actual_label": "anomaly"}
]

correct_predictions = 0
total_logs = len(dataset)

print("🚀 Запуск автономного эксперимента через Low-code пайплайн n8n...")

for index, item in enumerate(dataset):
    print(f"\nОтправка лога {index + 1}/{total_logs} в n8n...")
    
    try:
        # Стучимся ТОЛЬКО в визуальный интерфейс
        response = requests.post(N8N_WEBHOOK_URL, json={"log_text": item["log"]})
        
        # Получаем итоговый ответ прямо из n8n
        n8n_result = response.json()
        
        # ---> ДОБАВЬ ВОТ ЭТУ СТРОКУ ДЛЯ ОТЛАДКИ <---
        print(f"🔍 Сырой ответ системы: {n8n_result}") 
        
        predicted_status = n8n_result.get("status")
        predicted_label = "anomaly" if predicted_status == "anomaly_detected" else "normal"
        
        if predicted_label == item["actual_label"]:
            correct_predictions += 1
            print(f"✅ Успешно! Ожидали: {item['actual_label']}, Получили: {predicted_label}")
            if predicted_label == "anomaly":
                print(f"   🤖 RCA: {n8n_result.get('root_cause_analysis')}")
        else:
            print(f"❌ Ошибка! Ожидали: {item['actual_label']}, Получили: {predicted_label}")
            
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        
    time.sleep(1)

accuracy = (correct_predictions / total_logs) * 100
print("\n" + "="*40)
print(f"📊 ИТОГИ ЭКСПЕРИМЕНТА")
print(f"Accuracy: {accuracy}%")
print("="*40)