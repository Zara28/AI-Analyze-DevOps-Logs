import pandas as pd
import random

# --- НАСТРОЙКИ ---
INPUT_LOG_FILE = "E:\\archive logs\\BGL.log"        # Укажи имя своего исходного лог-файла (.log или .txt)
OUTPUT_CSV_FILE = "dataset_by_bgl.csv" # Имя итогового CSV-файла

# Включить сэмплирование (сборка фиксированного размера для тестов)
ENABLE_SAMPLING = True
NUM_NORMAL = 500   # Сколько взять нормальных логов
NUM_ANOMALY = 220  # Сколько взять аномальных логов

# Фиксируем seed для воспроизводимости результатов
random.seed(42)


def process_logs_by_dash_rule():
    normal_logs = []
    anomaly_logs = []

    print(f"1. Чтение и разбор файла {INPUT_LOG_FILE}...")

    try:
        with open(INPUT_LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_clean = line.strip()
                if not line_clean:
                    continue

                # ПРАВИЛО: начинается ли строка с дефиса/тире '-'
                if line_clean.startswith('-'):
                    # Сообщение НЕ тревожное -> normal
                    normal_logs.append(line_clean)
                else:
                    # Сообщение тревожное (нет дефиса в начале) -> anomaly
                    anomaly_logs.append(line_clean)

    except FileNotFoundError:
        print(f"[!] Ошибка: Файл '{INPUT_LOG_FILE}' не найден. Проверь имя и путь к файлу!")
        return
    except Exception as e:
        print(f"[!] Ошибка при чтении файла: {e}")
        return

    print(f"   Найдено нормальных логов (начинаются с '-'): {len(normal_logs)}")
    print(f"   Найдено аномальных логов (без '-'): {len(anomaly_logs)}")

    # Формирование итогового датасета
    if ENABLE_SAMPLING:
        print(f"\n2. Формирование сбалансированной выборки ({NUM_NORMAL} normal / {NUM_ANOMALY} anomaly)...")

        num_norm = min(len(normal_logs), NUM_NORMAL)
        num_anom = min(len(anomaly_logs), NUM_ANOMALY)

        sampled_normal = random.sample(normal_logs, num_norm)
        sampled_anomaly = random.sample(anomaly_logs, num_anom)

        dataset = []
        for log in sampled_normal:
            dataset.append({'log_text': log, 'label': 'normal'})
        for log in sampled_anomaly:
            dataset.append({'log_text': log, 'label': 'anomaly'})

        # Перемешиваем нормальные и аномальные логи
        random.shuffle(dataset)
        df_result = pd.DataFrame(dataset)

    else:
        print("\n2. Сохранение ВСЕХ обработанных логов из файла...")
        dataset = []
        for log in normal_logs:
            dataset.append({'log_text': log, 'label': 'normal'})
        for log in anomaly_logs:
            dataset.append({'log_text': log, 'label': 'anomaly'})

        df_result = pd.DataFrame(dataset)

    # Сохраняем в CSV
    df_result.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8')
    print(f"\n[Успех] Датасет сохранен в файл: {OUTPUT_CSV_FILE}")
    print("Распределение меток в итоговом файле:")
    print(df_result['label'].value_counts())


if __name__ == "__main__":
    process_logs_by_dash_rule()