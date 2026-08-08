import csv
import requests
import time

N8N_WEBHOOK_URL = "http://localhost:5678/webhook/5e8dea2f-fcac-48cd-b140-139f9b5d5894"  # <- Вставь свой URL!
CSV_FILE = "TraceBench_Test_Dataset.csv"

# Матрица ошибок (Confusion Matrix)
TP = 0  # True Positive (Аномалия определена как аномалия)
TN = 0  # True Negative (Норма определена как норма)
FP = 0  # False Positive (Норма ложно определена как аномалия)
FN = 0  # False Negative (Аномалия пропущена)

total_logs = 0
start_time = time.time()

print(f"🚀 Запуск массового тестирования гибридной модели. Чтение {CSV_FILE}...")

with open(CSV_FILE, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        log_text = row['log_text']
        actual_label = row['label']
        total_logs += 1

        print(f"\rОтправка лога [{total_logs}/{len(reader)}]...", end="")

        try:
            response = requests.post(N8N_WEBHOOK_URL, json={"log_text": log_text})
            n8n_result = response.json()
            predicted_status = str(n8n_result.get("status", "")).lower()  # Приводим к нижнему регистру

            # Делаем мягкий поиск слова-триггера
            if "anomaly" in predicted_status:
                predicted_label = "anomaly"
            else:
                predicted_label = "normal"

            # Подсчет для матрицы ошибок
            if actual_label == "anomaly" and predicted_label == "anomaly":
                TP += 1
            elif actual_label == "normal" and predicted_label == "normal":
                TN += 1
            elif actual_label == "normal" and predicted_label == "anomaly":
                FP += 1
            elif actual_label == "anomaly" and predicted_label == "normal":
                FN += 1

        except Exception as e:
            print(f"\n⚠️ Ошибка связи на логе {total_logs}: {e}")

        time.sleep(0.5)  # Небольшая задержка, чтобы не уронить n8n

# Расчет метрик
accuracy = (TP + TN) / total_logs if total_logs > 0 else 0
precision = TP / (TP + FP) if (TP + FP) > 0 else 0
recall = TP / (TP + FN) if (TP + FN) > 0 else 0
f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

execution_time = round(time.time() - start_time, 2)

print("\n\n" + "=" * 50)
print("📊 ИТОГИ МАССОВОГО ЭКСПЕРИМЕНТА")
print("=" * 50)
print(f"Обраработано логов: {total_logs} (Время: {execution_time} сек)")
print(f"Матрица ошибок: TP={TP}, TN={TN}, FP={FP}, FN={FN}")
print("-" * 50)
print(f"Accuracy (Точность общая): {accuracy:.4f}")
print(f"Precision (Точность аномалий): {precision:.4f}")
print(f"Recall (Полнота): {recall:.4f}")
print(f"F1-Score (F-мера): {f1_score:.4f}")
print("=" * 50)