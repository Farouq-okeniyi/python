import psycopg2
import importlib
import psutil
import time
import csv
import os
import math

# ========== Load AES Encryption Module ==========
AES = importlib.import_module("Encryption.aes_encryption")

# ========== PostgreSQL Grid Nodes ==========
grid_nodes = [
    {"dbname": "grid_node_1", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_2", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_3", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
]

# ========== CSV Setup ==========
CSV_FILE = "AES_METRICS_100KB_1stSample.csv"

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["operation", "iteration_number", "file_size_label",
                             "cpu_percent", "memory_used_mb", "process_time_sec", "encrypted_size_bytes"])

def log_to_csv(operation, iteration, file_size_label, cpu_percent, memory_used, process_time, encrypted_size):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([operation, iteration, file_size_label, cpu_percent, memory_used, process_time, encrypted_size])

# ========== Entropy Function ==========
def calculate_entropy(data):
    if not data:
        return 0
    byte_array = data.encode()  # assuming string data
    length = len(byte_array)
    freq = {}
    for b in byte_array:
        freq[b] = freq.get(b, 0) + 1

    entropy = 0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

# ========== Encryption Function ==========
def encrypt_and_log_all(source_conn, source_cursor, target_conn, target_cursor, label='100KB file', total_iterations=50):
    try:
        source_cursor.execute("SELECT text_to_encrypt FROM data_store WHERE file_size_label = %s LIMIT 1;", (label,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No plaintext found for label '{label}'")
            return

        plain_text = row[0]
        encrypted_result = None
        total_encrypted_bytes = 0
        entropy_value = 0

        start_total = time.perf_counter()

        for i in range(1, total_iterations + 1):
            encrypted, metrics = AES.encrypt(plain_text)
            encrypted_result = encrypted  # Hold the last encrypted result for DB saving later
            encrypted_bytes = encrypted.encode()
            encrypted_size = len(encrypted_bytes)
            total_encrypted_bytes += encrypted_size

            # Entropy calculation for the *last* ciphertext (we can average if you want)
            entropy_value = calculate_entropy(encrypted)

            log_to_csv("encryption", i, label, metrics["cpu_percent"], metrics["memory_diff_mb"], metrics["time_diff_sec"], encrypted_size)

        end_total = time.perf_counter()
        total_time = end_total - start_total
        throughput = total_encrypted_bytes / total_time if total_time > 0 else 0

        print(f"[INFO] Total encrypted data size (bytes): {total_encrypted_bytes}")
        print(f"[INFO] Total encryption time (seconds): {total_time:.4f}")
        print(f"[INFO] Encryption Throughput (bytes/sec): {throughput:.4f}")
        print(f"[INFO] Entropy of last ciphertext: {entropy_value:.4f} bits per byte")

        # Save only once after all iterations
        target_cursor.execute("UPDATE data_store SET AES_ENCRYPTION = %s WHERE file_size_label = %s;", (encrypted_result, label))
        target_conn.commit()

    except Exception as e:
        print(f"[ERROR - AES encryption] {e}")


# ========== Decryption Function ==========
def decrypt_and_log_all(source_conn, source_cursor, target_conn, target_cursor, label='100KB file', total_iterations=50):
    try:
        source_cursor.execute("SELECT AES_ENCRYPTION FROM data_store WHERE file_size_label = %s LIMIT 1;", (label,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No AES encrypted data found for label '{label}'")
            return

        encrypted_text = row[0]
        decrypted_result = None
        total_decrypted_bytes = 0

        start_total = time.perf_counter()

        for i in range(1, total_iterations + 1):
            decrypted, metrics = AES.decrypt(encrypted_text)
            decrypted_result = decrypted  # Save last decrypted result for DB saving later
            decrypted_bytes = decrypted.encode()
            decrypted_size = len(decrypted_bytes)
            total_decrypted_bytes += decrypted_size

            log_to_csv("decryption", i, label, metrics["cpu_percent"], metrics["memory_diff_mb"], metrics["time_diff_sec"], decrypted_size)

        end_total = time.perf_counter()
        total_time = end_total - start_total
        throughput = total_decrypted_bytes / total_time if total_time > 0 else 0

        print(f"[INFO] Total decrypted data size (bytes): {total_decrypted_bytes}")
        print(f"[INFO] Total decryption time (seconds): {total_time:.4f}")
        print(f"[INFO] Decryption Throughput (bytes/sec): {throughput:.4f}")

        # Save only once after all iterations
        target_cursor.execute("UPDATE data_store SET AES_DECRYPTION = %s WHERE file_size_label = %s;", (decrypted_result, label))
        target_conn.commit()

    except Exception as e:
        print(f"[ERROR - AES decryption] {e}")


# ========== Main ==========
if __name__ == "__main__":
    init_csv()

    try:
        conn1 = psycopg2.connect(**grid_nodes[0])
        cur1 = conn1.cursor()

        conn2 = psycopg2.connect(**grid_nodes[1])
        cur2 = conn2.cursor()

        conn3 = psycopg2.connect(**grid_nodes[2])
        cur3 = conn3.cursor()

        # ========== Run encryption & decryption ==========
        encrypt_and_log_all(conn1, cur1, conn2, cur2, label="100KB file", total_iterations=50)
        decrypt_and_log_all(conn2, cur2, conn3, cur3, label="100KB file", total_iterations=50)

    except Exception as e:
        print(f"[ERROR - main connection setup] {e}")

    finally:
        for conn, cur in [(conn1, cur1), (conn2, cur2), (conn3, cur3)]:
            try:
                if cur: cur.close()
                if conn: conn.close()
            except:
                pass
