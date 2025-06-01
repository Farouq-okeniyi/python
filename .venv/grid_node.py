import psycopg2
import importlib
import psutil
from prometheus_client import start_http_server, Summary, Gauge, Counter
import time

# ========== Configuration ==========
start_http_server(8000)

# ========== Prometheus Metrics ==========
REQUEST_TIME = Summary('crypto_processing_seconds', 'Time spent processing encryption/decryption')

CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage during crypto operations')
MEMORY_USAGE = Gauge('memory_usage_mb', 'Memory usage (MB) during crypto operations')

BYTES_ENCRYPTED = Counter('bytes_encrypted_total', 'Total number of bytes encrypted', ['file_size_label'])
ENCRYPTION_OPERATIONS = Counter('encryption_operations_total', 'Total encryption operations performed', ['file_size_label'])
ENCRYPTION_FAILURES = Counter('encryption_failures_total', 'Total failed encryption operations', ['file_size_label'])

DECRYPTION_OPERATIONS = Counter('decryption_operations_total', 'Total decryption operations performed', ['file_size_label'])
DECRYPTION_FAILURES = Counter('decryption_failures_total', 'Total failed decryption operations', ['file_size_label'])

ENCRYPTION_LOOP_ITERATIONS = Counter('encryption_loop_iterations_total', 'Total iterations of encryption loop', ['file_size_label'])

# ========== Load AES Encryption Module ==========
AES = importlib.import_module("Encryption.aes_encryption")

# ========== PostgreSQL Grid Nodes ==========
grid_nodes = [
    {"dbname": "grid_node_1", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_2", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_3", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
]

# ========== System Monitoring ==========
def get_system_usage():
    CPU_USAGE.set(psutil.cpu_percent(interval=1))
    MEMORY_USAGE.set(psutil.virtual_memory().used / (1024 * 1024))  # Convert to MB

# ========== Encryption Wrapper ==========
@REQUEST_TIME.time()
def encrypt_value(value: str):
    return AES.encrypt(value)

# ========== Decryption Wrapper ==========
@REQUEST_TIME.time()
def decrypt_value(encrypted_value: str):
    return AES.decrypt(encrypted_value)

# ========== Step 1: Insert Plaintext Files into Node 1 ==========
def insert_plaintext_files(conn, cursor, files):
    try:
        for size_label, filepath in files.items():
            with open(filepath, 'rb') as f:
                file_data = f.read()
            decoded_text = file_data.decode(errors='ignore')
            cursor.execute("""
                INSERT INTO data_store (file_size_label, text_to_encrypt)
                VALUES (%s, %s)
            """, (size_label, decoded_text))
        conn.commit()
    except Exception as e:
        print(f"[ERROR - file insert] {e}")

# ========== Step 2: Encrypt from Node 1 to Node 2 ==========
def encrypt_and_transfer(source_conn, source_cursor, target_conn, target_cursor, label='1MB file', iterations=250):
    try:
        source_cursor.execute("""
            SELECT text_to_encrypt FROM data_store 
            WHERE file_size_label = %s 
            LIMIT 1;
        """, (label,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No plaintext found for label '{label}'")
            return

        plain_text = row[0]

        for i in range(iterations):
            print(f"[INFO] Encryption loop iteration {i + 1} for {label}")
            get_system_usage()

            encrypted = encrypt_value(plain_text)

            BYTES_ENCRYPTED.labels(label).inc(len(plain_text.encode()))
            ENCRYPTION_OPERATIONS.labels(label).inc()
            ENCRYPTION_LOOP_ITERATIONS.labels(label).inc()

            target_cursor.execute("""
                UPDATE data_store 
                SET AES_ENCRYPTION = %s 
                WHERE file_size_label = %s;
            """, (encrypted, label))
            target_conn.commit()

            time.sleep(0.1)  # Slow down loop for better Prometheus visualization

    except Exception as e:
        ENCRYPTION_FAILURES.labels(label).inc()
        print(f"[ERROR - AES encryption] {e}")

# ========== Step 3: Decrypt from Node 2 to Node 3 ==========
def decrypt_and_store(source_conn, source_cursor, target_conn, target_cursor, label='1MB file', iterations=250):
    try:
        source_cursor.execute("""
            SELECT AES_ENCRYPTION FROM data_store 
            WHERE file_size_label = %s 
            LIMIT 1;
        """, (label,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No AES encrypted data found for label '{label}'")
            return

        encrypted_text = row[0]

        for i in range(iterations):
            print(f"[INFO] Decryption loop iteration {i + 1} for {label}")
            decrypted = decrypt_value(encrypted_text)

            DECRYPTION_OPERATIONS.labels(label).inc()

            target_cursor.execute("""
                UPDATE data_store 
                SET AES_DECRYPTION = %s 
                WHERE file_size_label = %s;
            """, (decrypted, label))
            target_conn.commit()

            time.sleep(0.1)

        print(f"[DONE] AES decryption complete for '{label}'")

    except Exception as e:
        DECRYPTION_FAILURES.labels(label).inc()
        print(f"[ERROR - AES decryption] {e}")

# ========== Main Execution ==========
if __name__ == "__main__":
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

        # Optional: Step 1
        # insert_plaintext_files(conn1, cur1, files)

        # Step 2: AES Encryption with Prometheus metrics
        encrypt_and_transfer(conn1, cur1, conn2, cur2, label="3MB file", iterations=250)

        # Optional: Step 3
        # decrypt_and_store(conn2, cur2, conn3, cur3, label="3MB file", iterations=250)

    except Exception as e:
        print(f"[ERROR - main connection setup] {e}")

    finally:
        for conn, cur in [(conn1, cur1), (conn2, cur2), (conn3, cur3)]:
            try:
                if cur: cur.close()
                if conn: conn.close()
            except:
                pass
