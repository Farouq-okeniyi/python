import psycopg2
import importlib
import psutil
import time
import csv
import os

# ========== Load AES Encryption Module ==========
AES = importlib.import_module("Encryption.aes_encryption")

# ========== PostgreSQL Grid Nodes ==========
grid_nodes = [
    {"dbname": "grid_node_1", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_2", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_3", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
]

# ========== CSV Setup ==========
CSV_FILE = "crypto_metrics.csv"

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["operation", "iteration", "file_size_label", "cpu_percent", "memory_used_mb", "time_seconds"])

def log_to_csv(operation, iteration, file_size_label, cpu_percent, memory_used, time_taken):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([operation, iteration, file_size_label, cpu_percent, memory_used, time_taken])

# Encryption Function
def encrypt_and_transfer(source_conn, source_cursor, target_conn, target_cursor, label='100KB file', iterations=50):
    try:
        source_cursor.execute("SELECT text_to_encrypt FROM data_store WHERE file_size_label = %s LIMIT 1;", (label,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No plaintext found for label '{label}'")
            return

        plain_text = row[0]
        encrypted = None

        for i in range(1, iterations + 1):
            print(f"[INFO] Encryption iteration {i} for {label}")

            encrypted, metrics = AES.encrypt(plain_text)

            log_to_csv("encryption", i, label, metrics["cpu_diff"], metrics["memory_diff_mb"], metrics["time_diff_sec"])

        target_cursor.execute("UPDATE data_store SET AES_ENCRYPTION = %s WHERE file_size_label = %s;", (encrypted, label))
        target_conn.commit()
        print(f"[DONE] Encryption complete for '{label}'")

    except Exception as e:
        print(f"[ERROR - AES encryption] {e}")


# Decryption Function
def decrypt_and_store(source_conn, source_cursor, target_conn, target_cursor, label='100KB file', iterations=50):
    try:
        source_cursor.execute("SELECT AES_ENCRYPTION FROM data_store WHERE file_size_label = %s LIMIT 1;", (label,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No AES encrypted data found for label '{label}'")
            return

        encrypted_text = row[0]

        for i in range(1, iterations + 1):
            print(f"[INFO] Decryption iteration {i} for '{label}'")

            decrypted, metrics = AES.decrypt(encrypted_text)

            log_to_csv("decryption", i, label, metrics["cpu_diff"], metrics["memory_diff_mb"], metrics["time_diff_sec"])

            target_cursor.execute("UPDATE data_store SET AES_DECRYPTION = %s WHERE file_size_label = %s;", (decrypted, label))
            target_conn.commit()

        print(f"[DONE] Decryption complete for '{label}'")

    except Exception as e:
        print(f"[ERROR - AES decryption] {e}")

# ========== Main ==========
if __name__ == "__main__":
    init_csv()

    files = {
        "100KB file": "C:/Users/USER/Documents/pythonfinal/100KB.txt",
        "500KB file": "C:/Users/USER/Documents/pythonfinal/500KB.txt",
        "1MB file": "C:/Users/USER/Documents/pythonfinal/1MB.txt",
        "2MB file": "C:/Users/USER/Documents/pythonfinal/2MB.txt",
        "3MB file": "C:/Users/USER/Documents/pythonfinal/3MB.txt",
        "4MB file": "C:/Users/USER/Documents/pythonfinal/4MB.txt",
        "5MB file": "C:/Users/USER/Documents/pythonfinal/5MB.txt",
    }

    try:
        conn1 = psycopg2.connect(**grid_nodes[0])
        cur1 = conn1.cursor()

        conn2 = psycopg2.connect(**grid_nodes[1])
        cur2 = conn2.cursor()

        conn3 = psycopg2.connect(**grid_nodes[2])
        cur3 = conn3.cursor()

        # Optional: insert_plaintext_files(conn1, cur1, files)

        # Run Encryption
        encrypt_and_transfer(conn1, cur1, conn2, cur2, label="100KB file", iterations=50)

        # Run Decryption
        decrypt_and_store(conn2, cur2, conn3, cur3, label="100KB file", iterations=50)

    except Exception as e:
        print(f"[ERROR - main connection setup] {e}")

    finally:
        for conn, cur in [(conn1, cur1), (conn2, cur2), (conn3, cur3)]:
            try:
                if cur: cur.close()
                if conn: conn.close()
            except:
                pass
