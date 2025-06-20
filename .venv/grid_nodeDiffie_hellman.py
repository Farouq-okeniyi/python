import psycopg2
import importlib
import psutil
import time
import csv
import os
import math

# ======================== CONFIGURATION ========================
LABEL = '100KB file'
TOTAL_ITERATIONS = 10
CSV_FILE = "DIFFIE_HELLMAN_METRICS_100KB.csv"

grid_nodes = [
    {"dbname": "grid_node_1", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_2", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_3", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
]

# ======================== MODULES ========================
DH = importlib.import_module("Encryption.Diffie_hellman")

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

def encrypt_and_log_all(source_conn, source_cursor, target_conn, target_cursor, shared_key):
    try:
        source_cursor.execute("SELECT text_to_encrypt FROM data_store WHERE file_size_label = %s LIMIT 1;", (LABEL,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No plaintext found for label '{LABEL}'")
            return

        plain_text = row[0]
        encrypted_result = None
        total_encrypted_bytes = 0

        for i in range(1, TOTAL_ITERATIONS + 1):
            encrypted, metrics = DH.encrypt(plain_text, shared_key)
            encrypted_result = encrypted
            encrypted_bytes = encrypted.encode()
            encrypted_size = len(encrypted_bytes)
            total_encrypted_bytes += encrypted_size

            log_to_csv("encryption", i, LABEL, metrics["cpu_percent"], metrics["memory_diff_mb"], metrics["time_diff_sec"], encrypted_size)

        entropy_value = calculate_entropy(encrypted_result)

        target_cursor.execute("UPDATE data_store SET DIFFIE_HELLMAN_ENCRYPTION = %s WHERE file_size_label = %s;", (encrypted_result, LABEL))
        target_conn.commit()

    except Exception as e:
        print(f"[ERROR - DH encryption] {e}")

def decrypt_and_log_all(source_conn, source_cursor, target_conn, target_cursor, shared_key):
    try:
        source_cursor.execute("SELECT DIFFIE_HELLMAN_ENCRYPTION FROM data_store WHERE file_size_label = %s LIMIT 1;", (LABEL,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No Diffie-Hellman encrypted data found for label '{LABEL}'")
            return

        encrypted_text = row[0]
        decrypted_result = None
        total_decrypted_bytes = 0

        for i in range(1, TOTAL_ITERATIONS + 1):
            decrypted, metrics = DH.decrypt(encrypted_text, shared_key)
            decrypted_result = decrypted
            decrypted_bytes = decrypted.encode()
            decrypted_size = len(decrypted_bytes)
            total_decrypted_bytes += decrypted_size

            log_to_csv("decryption", i, LABEL, metrics["cpu_percent"], metrics["memory_diff_mb"], metrics["time_diff_sec"], decrypted_size)

        target_cursor.execute("UPDATE data_store SET DIFFIE_HELLMAN_DECRYPTION = %s WHERE file_size_label = %s;", (decrypted_result, LABEL))
        target_conn.commit()

    except Exception as e:
        print(f"[ERROR - DH decryption] {e}")

if __name__ == "__main__":
    init_csv()
    try:
        conn1 = psycopg2.connect(**grid_nodes[0])
        cur1 = conn1.cursor()

        conn2 = psycopg2.connect(**grid_nodes[1])
        cur2 = conn2.cursor()

        conn3 = psycopg2.connect(**grid_nodes[2])
        cur3 = conn3.cursor()

        # Generate shared secret for both encryption/decryption
        P = DH.P
        G = DH.G
        a_private = DH.generate_private_key(P)
        a_public = DH.generate_public_key(a_private, G, P)

        b_private = DH.generate_private_key(P)
        b_public = DH.generate_public_key(b_private, G, P)

        shared_key = DH.compute_shared_secret(b_public, a_private, P)

        encrypt_and_log_all(conn1, cur1, conn2, cur2, shared_key)
        decrypt_and_log_all(conn2, cur2, conn3, cur3, shared_key)

    except Exception as e:
        print(f"[ERROR - main connection setup] {e}")

    finally:
        for conn, cur in [(conn1, cur1), (conn2, cur2), (conn3, cur3)]:
            try:
                if cur: cur.close()
                if conn: conn.close()
            except:
                pass
