import pandas as pd
import re
import random

# Фиксируем генератор случайных чисел для воспроизводимости
random.seed(42)

# --- НАСТРОЙКИ (укажи свои имена файлов при необходимости) ---
LOG_FILE = "E:\\archive logs\\HDFS_v1\\HDFS.log"         # или "HDFS.log"
LABELS_FILE = "E:\\archive logs\\HDFS_v1\\preprocessed\\anomaly_label.csv" # файл с метками блоков
OUTPUT_FILE = "HDFS_Test_Dataset.csv"

NUM_NORMAL = 500   # Сколько взять нормальных логов
NUM_ANOMALY = 220  # Сколько взять аномальных логов


def create_hdfs_test_dataset():
    print("1. Чтение меток блоков из anomaly_label.csv...")
    try:
        labels_df = pd.read_csv(LABELS_FILE)
    except Exception as e:
        print(f"Ошибка чтения {LABELS_FILE}: {e}")
        return

    # Создаем словарь: BlockId -> 'normal' или 'anomaly'
    block_labels = {}
    for _, row in labels_df.iterrows():
        block_id = str(row['BlockId']).strip()
        label = str(row['Label']).strip().lower()
        block_labels[block_id] = 'anomaly' if label == 'anomaly' else 'normal'

    print(f"   Загружено меток блоков: {len(block_labels)}")

    print("\n2. Парсинг лог-файла и сопоставление меток...")
    normal_logs = []
    anomaly_logs = []

    # Регулярное выражение для поиска BlockId (например, blk_-1608999687919862906 или blk_75039201)
    block_pattern = re.compile(r"(blk_[-\d]+)")

    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_clean = line.strip()
                if not line_clean:
                    continue

                # Ищем BlockId в текущей строке лога
                match = block_pattern.search(line_clean)
                if match:
                    block_id = match.group(1)

                    # Если данный блок есть в карте меток, относим лог к соответствующему списку
                    if block_id in block_labels:
                        if block_labels[block_id] == 'anomaly':
                            anomaly_logs.append(line_clean)
                        else:
                            normal_logs.append(line_clean)
    except Exception as e:
        print(f"Ошибка чтения лог-файла {LOG_FILE}: {e}")
        return

    print(f"   Найдено нормальных логов: {len(normal_logs)}")
    print(f"   Найдено аномальных логов: {len(anomaly_logs)}")

    # Проверяем, достаточно ли данных
    if len(normal_logs) < NUM_NORMAL or len(anomaly_logs) < NUM_ANOMALY:
        print(f"\n[!] Ошибка: Недостаточно логов! Требуется минимум {NUM_NORMAL} normal и {NUM_ANOMALY} anomaly.")
        return

    print(f"\n3. Выборка {NUM_NORMAL} нормальных и {NUM_ANOMALY} аномальных логов...")
    # Берем случайные уникальные логи
    sampled_normal = random.sample(normal_logs, NUM_NORMAL)
    sampled_anomaly = random.sample(anomaly_logs, NUM_ANOMALY)

    # Собираем единый список
    dataset = []
    for log in sampled_normal:
        dataset.append({'log_text': log, 'label': 'normal'})

    for log in sampled_anomaly:
        dataset.append({'log_text': log, 'label': 'anomaly'})

    # Перемешиваем выборку
    random.shuffle(dataset)

    # Сохраняем в CSV
    df_result = pd.DataFrame(dataset)
    df_result.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    print(f"\n[Успех] Файл {OUTPUT_FILE} успешно создан!")
    print("\nСостав сформированного датасета:")
    print(df_result['label'].value_counts())


if __name__ == "__main__":
    create_hdfs_test_dataset()