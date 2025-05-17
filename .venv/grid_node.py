# import psycopg2
# import importlib
# import time
# import psutil
# from prometheus_client import start_http_server, Summary, Gauge, Counter
# import os
# # =========1= Configuration ==========

# # Start Prometheus HTTP server
# start_http_server(8000)
# print("Prometheus server running on port 8000...")

# # Prometheus Metrics
# REQUEST_TIME = Summary('encryption_request_processing_seconds', 'Time spent processing encryption per request')
# CPU_USAGE = Gauge('encryption_cpu_usage_percent', 'CPU usage percentage during encryption')
# MEMORY_USAGE = Gauge('encryption_memory_usage_kb', 'Memory usage (kb) during encryption')
# BYTES_ENCRYPTED = Counter('encryption_bytes_total', 'Total number of bytes encrypted')
# ENCRYPTION_OPERATIONS = Counter('encryption_operations_total', 'Total encryption operations performed')
# ENCRYPTION_FAILURES = Counter('encryption_failures_total', 'Total failed encryption operations')

# # Load encryption module (make sure it has `encrypt()` and `decrypt()` functions)
# encryption_module = importlib.import_module("Encryption.aes_encryption")

# # Grid nodes
# grid_nodes = [
#     {"dbname": "grid_node_1", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
#     {"dbname": "grid_node_2", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
#     {"dbname": "grid_node_3", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
# ]

# # ========== Helper Functions ==========

# def get_system_usage():
#     CPU_USAGE.set(psutil.cpu_percent(interval=1))
#     MEMORY_USAGE.set(psutil.virtual_memory().used / (1024 * 1024))

# with open("C:\\Users\\USER\\Documents\\pythonfinal\\1MB.txt", 'rb') as f:
#     file_data = f.read()

# def encrypt_value(value):
#     @REQUEST_TIME.time()
#     def process():
#         return encryption_module.encrypt(value)
#     return process()

# def decrypt_value(encrypted_value):
#     @REQUEST_TIME.time()
#     def process():
#         return encryption_module.decrypt(encrypted_value)
#     return process()

# # ========== Main Function ==========

# def encrypt_and_transfer_one_row(source_node, target_node):
#     try:
#         print(f"\n[INFO] Connecting to source: {source_node['dbname']}")
#         source_conn = psycopg2.connect(**source_node)
#         source_cursor = source_conn.cursor()

#         source_cursor.execute("SELECT id, text_to_encrypt FROM data_store LIMIT 1;")
#         row = source_cursor.fetchone()

#         if not row:
#             print("[WARN] No data found in source node.")
#             return

#         row_id, text_to_encrypt = row
#         # print(f"[DATA] id={row_id}, text_to_encrypt={text_to_encrypt}")  

#         # Encrypt the `text_to_encrypt`
#         get_system_usage()
#         encrypted_text = encrypt_value(str(file_data))

#         # Decrypt the `encrypted_text` to verify it
#         decrypted_text = decrypt_value(encrypted_text)

#         BYTES_ENCRYPTED.inc(len(str(text_to_encrypt).encode()))
#         ENCRYPTION_OPERATIONS.inc()

#         # print(f"[INFO] Connecting to target: {target_node['dbname']}")
#         target_conn = psycopg2.connect(**target_node)
#         target_cursor = target_conn.cursor()

#         target_cursor.execute(
#             "INSERT INTO data_store (text_to_encrypt, encrypted_text, decrypted_text) VALUES (%s, %s, %s);",
#             (text_to_encrypt, encrypted_text, decrypted_text)
#         )
#         target_conn.commit()

#         # print(f" Encrypted and decrypted row inserted into {target_node['dbname']}")
#         # print(f"[ENCRYPTED VALUE] {str(encrypted_text)[:30]}...\n")

#         # Clean up
#         # source_cursor.close()
#         # source_conn.close()
#         # target_cursor.close()
#         # target_conn.close()

#     except Exception as e:
#         ENCRYPTION_FAILURES.inc()
#         print(f"[ERROR] {e}")

# if __name__ == "__main__":
#     for i in range(250):
#         print(f"\n[RUNNING ITERATION] {i+1}/240")
#         encrypt_and_transfer_one_row(grid_nodes[0], grid_nodes[1])



import psycopg2
import importlib
import time
import psutil
from prometheus_client import start_http_server, Summary, Gauge, Counter
import os

# ========== Configuration ==========
start_http_server(8000)
print("Prometheus server running on port 8000...")

# Prometheus Metrics
REQUEST_TIME = Summary('encryption_request_processing_seconds', 'Time spent processing encryption per request')
CPU_USAGE = Gauge('encryption_cpu_usage_percent', 'CPU usage percentage during encryption')
MEMORY_USAGE = Gauge('encryption_memory_usage_kb', 'Memory usage (MB) during encryption')
BYTES_ENCRYPTED = Counter('encryption_bytes_total', 'Total number of bytes encrypted')
ENCRYPTION_OPERATIONS = Counter('encryption_operations_total', 'Total encryption operations performed')
ENCRYPTION_FAILURES = Counter('encryption_failures_total', 'Total failed encryption operations')

# Load custom encryption module
encryption_module = importlib.import_module("Encryption.aes_encryption")

# PostgreSQL node configs
grid_nodes = [
    {"dbname": "grid_node_1", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_2", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_3", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
]

# ========== Utility Functions ==========

def get_system_usage():
    CPU_USAGE.set(psutil.cpu_percent(interval=1))
    MEMORY_USAGE.set(psutil.virtual_memory().used / (1024 * 1024))  # MB

@REQUEST_TIME.time()
def encrypt_value(value: str):
    return encryption_module.encrypt(value)

@REQUEST_TIME.time()
def decrypt_value(encrypted_value: str):
    return encryption_module.decrypt(encrypted_value)

# ========== Step 1: Insert Plaintext Files into Node 1 ==========

def insert_plaintext_files(node, files):
    try:
        conn = psycopg2.connect(**node)
        cursor = conn.cursor()

        for size_label, filepath in files.items():
            with open(filepath, 'rb') as f:
                file_data = f.read()

            decoded_text = file_data.decode(errors='ignore')

            cursor.execute("""
                INSERT INTO data_store (file_size_label, plain_text, text_to_encrypt)
                VALUES (%s, %s, %s)
            """, (size_label, decoded_text, decoded_text))
            print(f"[INSERTED] {size_label} into Node 1")

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR - insert_plaintext_files] {e}")

# ========== Step 2: Encrypt from Node 1 to Node 2 ==========

def encrypt_and_transfer_plaintext(source_node, target_node):
    try:
        conn = psycopg2.connect(**source_node)
        cursor = conn.cursor()
        cursor.execute("SELECT id, text_to_encrypt, file_size_label FROM data_store WHERE encrypted_text IS NULL;")
        rows = cursor.fetchall()

        for row in rows:
            row_id, plain_text, label = row
            get_system_usage()
            encrypted = encrypt_value(plain_text)

            BYTES_ENCRYPTED.inc(len(plain_text.encode()))
            ENCRYPTION_OPERATIONS.inc()

            target_conn = psycopg2.connect(**target_node)
            target_cursor = target_conn.cursor()
            target_cursor.execute("""
                INSERT INTO data_store (file_size_label, text_to_encrypt, encrypted_text)
                VALUES (%s, %s, %s)
            """, (label, plain_text, encrypted))
            target_conn.commit()
            target_cursor.close()
            target_conn.close()

        cursor.close()
        conn.close()

    except Exception as e:
        ENCRYPTION_FAILURES.inc()
        print(f"[ERROR - encryption] {e}")

# ========== Step 3: Decrypt from Node 2 to Node 3 ==========

def decrypt_and_transfer_encrypted(source_node, target_node):
    try:
        conn = psycopg2.connect(**source_node)
        cursor = conn.cursor()
        cursor.execute("SELECT id, encrypted_text, file_size_label FROM data_store WHERE decrypted_text IS NULL;")
        rows = cursor.fetchall()

        for row in rows:
            row_id, encrypted_text, label = row
            decrypted = decrypt_value(encrypted_text)

            target_conn = psycopg2.connect(**target_node)
            target_cursor = target_conn.cursor()
            target_cursor.execute("""
                INSERT INTO data_store (file_size_label, encrypted_text, decrypted_text)
                VALUES (%s, %s, %s)
            """, (label, encrypted_text, decrypted))
            target_conn.commit()
            target_cursor.close()
            target_conn.close()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR - decryption] {e}")

# ========== Run All Steps ==========

if __name__ == "__main__":
    files = {
        "100KB file": "C:/Users/USER/Documents/pythonfinal/100KB.txt",
        "500KB file": "C:/Users/USER/Documents/pythonfinal/500KB.txt",
        "1MB file": "C:/Users/USER/Documents/pythonfinal/1MB.txt",
        "2MB file": "C:/Users/USER/Documents/pythonfinal/2MB.txt",
        "Another 1MB file": "C:/Users/USER/Documents/pythonfinal/1MB_2.txt"
    }

    print("[STEP 1] Inserting plaintext files into Node 1...")
    insert_plaintext_files(grid_nodes[0], files)

    print("[STEP 2] Encrypting from Node 1 to Node 2...")
    encrypt_and_transfer_plaintext(grid_nodes[0], grid_nodes[1])

    print("[STEP 3] Decrypting from Node 2 to Node 3...")
    decrypt_and_transfer_encrypted(grid_nodes[1], grid_nodes[2])
