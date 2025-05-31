import psycopg2
import importlib
import psutil
from prometheus_client import start_http_server, Summary, Gauge, Counter

# ========== Configuration ==========
start_http_server(8000)
print("✅ Prometheus metrics server running on http://localhost:8000")

# ========== Prometheus Metrics ==========
REQUEST_TIME = Summary('crypto_processing_seconds', 'Time spent processing encryption/decryption')

CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage during crypto operations')
MEMORY_USAGE = Gauge('memory_usage_mb', 'Memory usage (MB) during crypto operations')

BYTES_ENCRYPTED = Counter('bytes_encrypted_total', 'Total number of bytes encrypted')
ENCRYPTION_OPERATIONS = Counter('encryption_operations_total', 'Total encryption operations performed')
ENCRYPTION_FAILURES = Counter('encryption_failures_total', 'Total failed encryption operations')

DECRYPTION_OPERATIONS = Counter('decryption_operations_total', 'Total decryption operations performed')
DECRYPTION_FAILURES = Counter('decryption_failures_total', 'Total failed decryption operations')

# ========== Load AES Encryption Module ==========
# AES = importlib.import_module("Encryption.aes_encryption")
# BLOWFISH = importlib.import_module("Encryption.blowfish_encryption")
# ECC = importlib.import_module("Encryption.ecc_encryption")
# RSA = importlib.import_module("Encryption.rsa_encryption")
CHACHA20 = importlib.import_module("Encryption.chacha20")

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
    return CHACHA20.encrypt(value)

# ========== Decryption Wrapper ==========
@REQUEST_TIME.time()
def decrypt_value(encrypted_value: str):
    return CHACHA20.decrypt(encrypted_value)

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
        print("[INFO] Inserted plaintext files.")
    except Exception as e:
        print(f"[ERROR - insert_plaintext_files] {e}")

# ========== Step 2: Encrypt from Node 1 to Node 2 ==========
def encrypt_and_transfer(source_conn, source_cursor, target_conn, target_cursor, label='1MB file', iterations=2):
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
            get_system_usage()
            encrypted = encrypt_value(plain_text)

            BYTES_ENCRYPTED.inc(len(plain_text.encode()))
            ENCRYPTION_OPERATIONS.inc()

            target_cursor.execute("""
                UPDATE data_store 
                SET CHACHA20_ENCRYPTION = %s 
                WHERE file_size_label = %s;
            """, (encrypted, label))
            target_conn.commit()

        print(f"[DONE] CHACHA20 encryption complete for '{label}'")

    except Exception as e:
        ENCRYPTION_FAILURES.inc()
        print(f"[ERROR - CHACHA20 encryption] {e}")

# ========== Step 3: Decrypt from Node 2 to Node 3 ==========


def decrypt_and_store(source_conn, source_cursor, target_conn, target_cursor, label='1MB file', iterations=2):
    try:
        source_cursor.execute("""
            SELECT CHACHA20_ENCRYPTION FROM data_store 
            WHERE file_size_label = %s 
            LIMIT 1;
        """, (label,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No CHACHA20 encrypted data found for label '{label}'")
            return

        encrypted_text = row[0]

        for i in range(iterations):
            decrypted = decrypt_value(encrypted_text)

            target_cursor.execute("""
                UPDATE data_store 
                SET CHACHA20_DECRYPTION = %s 
                WHERE file_size_label = %s;
            """, (decrypted, label))
            target_conn.commit()

        print(f"[DONE] CHACHA20 decryption complete for '{label}'")

    except Exception as e:
        DECRYPTION_FAILURES.inc()
        print(f"[ERROR - ECC decryption] {e}")


def store_encrypted_text(target_cursor, target_conn, label: str, plain_text: str):
    encrypted_text = encrypt_value(plain_text)
    target_cursor.execute("""
        UPDATE data_store
        SET encrypted_text = %s
        WHERE file_size_label = %s;
    """, (encrypted_text, label))
    target_conn.commit()

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

        # [OPTIONAL] Step 1: Insert plaintext files into Node 1 
        # insert_plaintext_files(conn1, cur1, files)

        # Step 2: Encrypt from Node 1 to Node 2 for aes encrption
        # encrypt_and_transfer(conn1, cur1, conn2, cur2, label="3MB file", iterations=2)

        # Step 3: Decrypt from Node 2 to Node 3 for aes decrption
        decrypt_and_store(c onn2, cur2, conn3, cur3, label="3MB file", iterations=2)

    except Exception as e:
        print(f"[ERROR - main connection setup] {e}")

    finally:
        for conn, cur in [(conn1, cur1), (conn2, cur2), (conn3, cur3)]:
            try:
                if cur: cur.close()
                if conn: conn.close()
            except:
                pass
