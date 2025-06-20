import psycopg2
import importlib
import psutil
import time
import csv
import os
import math

# ======================== CONFIGURATION ========================
LABEL = '3MB file'
TOTAL_ITERATIONS = 100
NUMBER_OF_TRIES = 4  # Set this to how many tries/files you want to generate
BASE_CSV_NAME = "ECC_METRICS_3MB_" + str(TOTAL_ITERATIONS) + "ITERATIONS"

# ======================== MODULES ========================
ECC = importlib.import_module("Encryption.ecc_encryption")

grid_nodes = [
    {"dbname": "grid_node_1", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_2", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_3", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
]

def get_csv_file_name(try_number):
    suffix = {1: "1sttry", 2: "2ndtry", 3: "3rdtry"}.get(try_number, f"{try_number}thtry")
    return f"{BASE_CSV_NAME}_{suffix}.csv"

def init_csv(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["operation", "iteration_number", "file_size_label",
                         "cpu_percent", "memory_used_mb", "process_time_sec", "encrypted_size_bytes"])

def log_to_csv(csv_file, operation, iteration, file_size_label, cpu_percent, memory_used, process_time, encrypted_size):
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([operation, iteration, file_size_label, cpu_percent, memory_used, process_time, encrypted_size])

def calculate_entropy(data):
    if not data:
        return 0
    byte_array = data.encode()
    length = len(byte_array)
    freq = {}
    for b in byte_array:
        freq[b] = freq.get(b, 0) + 1
    entropy = 0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def encrypt_and_log_all(source_conn, source_cursor, target_conn, target_cursor, csv_file):
    try:
        source_cursor.execute("SELECT text_to_encrypt FROM data_store WHERE file_size_label = %s LIMIT 1;", (LABEL,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No plaintext found for label '{LABEL}'")
            return

        plain_text = row[0]
        encrypted_result = None

        for i in range(1, TOTAL_ITERATIONS + 1):
            encrypted, metrics = ECC.encrypt(plain_text)
            encrypted_result = encrypted
            encrypted_bytes = encrypted.encode()
            encrypted_size = len(encrypted_bytes)

            log_to_csv(csv_file, "encryption", i, LABEL, metrics["cpu_percent"], metrics["memory_diff_mb"], metrics["time_diff_sec"], encrypted_size)

        entropy_value = calculate_entropy(encrypted_result)

        target_cursor.execute("UPDATE data_store SET AES_ENCRYPTION = %s WHERE file_size_label = %s;", (encrypted_result, LABEL))
        target_conn.commit()

    except Exception as e:
        print(f"[ERROR - AES encryption] {e}")

def decrypt_and_log_all(source_conn, source_cursor, target_conn, target_cursor, csv_file):
    try:
        source_cursor.execute("SELECT AES_ENCRYPTION FROM data_store WHERE file_size_label = %s LIMIT 1;", (LABEL,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No AES encrypted data found for label '{LABEL}'")
            return

        encrypted_text = row[0]
        decrypted_result = None

        for i in range(1, TOTAL_ITERATIONS + 1):
            decrypted, metrics = ECC.decrypt(encrypted_text)
            decrypted_result = decrypted
            decrypted_bytes = decrypted.encode()
            decrypted_size = len(decrypted_bytes)

            log_to_csv(csv_file, "decryption", i, LABEL, metrics["cpu_percent"], metrics["memory_diff_mb"], metrics["time_diff_sec"], decrypted_size)

        target_cursor.execute("UPDATE data_store SET AES_DECRYPTION = %s WHERE file_size_label = %s;", (decrypted_result, LABEL))
        target_conn.commit()

    except Exception as e:
        print(f"[ERROR - AES decryption] {e}")

if __name__ == "__main__":
    for try_number in range(1, NUMBER_OF_TRIES + 1):
        csv_file = get_csv_file_name(try_number)
        print(f"[INFO] Running Try #{try_number}: Logging to {csv_file}")
        init_csv(csv_file)
        try:
            conn1 = psycopg2.connect(**grid_nodes[0])
            cur1 = conn1.cursor()

            conn2 = psycopg2.connect(**grid_nodes[1])
            cur2 = conn2.cursor()

            conn3 = psycopg2.connect(**grid_nodes[2])
            cur3 = conn3.cursor()

            encrypt_and_log_all(conn1, cur1, conn2, cur2, csv_file)
            decrypt_and_log_all(conn2, cur2, conn3, cur3, csv_file)

        except Exception as e:
            print(f"[ERROR - main connection setup] {e}")

        finally:
            for conn, cur in [(locals().get('conn1'), locals().get('cur1')),
                              (locals().get('conn2'), locals().get('cur2')),
                              (locals().get('conn3'), locals().get('cur3'))]:
                try:
                    if cur: cur.close()
                    if conn: conn.close()
                except:
                    # pass
                    print("Abdul-Quayyum Was Here!!!")
