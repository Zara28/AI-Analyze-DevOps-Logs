import csv
import glob
import re
import pandas as pd
import random

# Фиксируем случайность для воспроизводимости выборки
random.seed(42)

# --- НАСТРОЙКИ ---
DATAPATH = 'e:\\archive logs\\HDFS_v3_TraceBench\\tracebench\\*\\event.csv'
OUTPUT_FILE = 'TraceBench_Test_Dataset.csv'

# Количество логов для выборки (можешь изменить при необходимости)
NUM_NORMAL = 80
NUM_ANOMALY = 20


def create_tracebench_dataset():
    datafiles = glob.glob(DATAPATH)
    if not datafiles:
        print(f"[!] Файлы не найдены по пути: {DATAPATH}")
        print("Убедись, что папка 'tracebench' с подпапками находится рядом со скриптом.")
        return

    # Регулярка для очистки логов от конкретных цифр (как в оригинальном data_process.py)
    digit_pattern = r'[0-9][^a-z^/]*'

    normal_logs = set()   # Используем set, чтобы автоматически исключить дубликаты
    anomaly_logs = set()

    print("1. Сканирование и обработка файлов TraceBench...")
    for datafile in datafiles:
        try:
            with open(datafile, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f, delimiter=',')
                header = next(reader, None)  # Пропускаем заголовок CSV

                is_normal_file = 'NM_' in datafile

                for row in reader:
                    if len(row) < 9:
                        continue

                    event_type = row[2].strip()
                    raw_desc = row[8].strip()

                    # Очищаем описание от чисел/таймстемпов, формируя чистый текст лога
                    clean_desc = re.sub(digit_pattern, '', raw_desc.lower()).strip()
                    log_text = f"{event_type}: {clean_desc}"

                    if is_normal_file:
                        normal_logs.add(log_text)
                    else:
                        # В папках AN_ и COM_ проверяем оригинал правила аномалии
                        desc_lower = raw_desc.lower()
                        if 'success:' not in desc_lower and 'a user task' not in desc_lower:
                            anomaly_logs.add(log_text)
                        else:
                            normal_logs.add(log_text)
        except Exception as e:
            print(f"Ошибка при обработке {datafile}: {e}")

    normal_list = list(normal_logs)
    anomaly_list = list(anomaly_logs)

    print(f"   Найдено уникальных нормальных логов: {len(normal_list)}")
    print(f"   Найдено уникальных аномальных логов: {len(anomaly_list)}")

    # Выборка нужного количества логов
    num_norm = min(len(normal_list), NUM_NORMAL)
    num_anom = min(len(anomaly_list), NUM_ANOMALY)

    print(f"\n2. Формирование выборки ({num_norm} normal / {num_anom} anomaly)...")
    sampled_normal = random.sample(normal_list, num_norm)
    sampled_anomaly = random.sample(anomaly_list, num_anom)

    dataset = []
    for log in sampled_normal:
        dataset.append({'log_text': log, 'label': 'normal'})

    for log in sampled_anomaly:
        dataset.append({'log_text': log, 'label': 'anomaly'})

    # Перемешиваем нормальные и аномальные логи
    random.shuffle(dataset)

    # Сохраняем в CSV
    df = pd.DataFrame(dataset)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    print(f"\n[Успех] Файл {OUTPUT_FILE} создан!")
    print(df['label'].value_counts())


if __name__ == "__main__":
    create_tracebench_dataset()