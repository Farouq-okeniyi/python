import psycopg2
import importlib
import psutil
import time
import csv
import os
import math
from Crypto.Util.Padding import pad, unpad
from psycopg2 import Binary
import base64

# ======================== CONFIGURATION ========================
LABEL = '3MB file'
TOTAL_ITERATIONS = 50

TRY_NUMBER = 4 # or however you want to increment for different runs


BLOWFISH_BLOCK_SIZE = 8  # Blowfish block size

# ======================== MODULES ========================
BLOWFISH = importlib.import_module("Encryption.blowfish_encryption")

grid_nodes = [
    {"dbname": "grid_node_1", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_2", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_3", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
]

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["operation", "iteration_number", "file_size_label",
                             "cpu_percent", "memory_used_mb", "process_time_sec", "encrypted_size_bytes", "entropy"])

def log_to_csv(operation, iteration, file_size_label, cpu_percent, memory_used, process_time, encrypted_size, entropy):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([operation, iteration, file_size_label, cpu_percent, memory_used, process_time, encrypted_size, entropy])

def calculate_entropy(data: bytes):
    if not data:
        return 0
    length = len(data)
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    entropy = 0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def encrypt_and_log_all(source_conn, source_cursor, target_conn, target_cursor):
    """Using hex storage approach for better compatibility"""
    try:
        source_cursor.execute("SELECT text_to_encrypt FROM data_store WHERE file_size_label = %s LIMIT 1;", (LABEL,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No plaintext found for label '{LABEL}'")
            return

        plain_text = row[0]
        encrypted_result = None

        for i in range(1, TOTAL_ITERATIONS + 1):
            encrypted_b64, metrics = BLOWFISH.encrypt(plain_text)
            encrypted_result = encrypted_b64
            
            # Convert base64 to bytes to calculate entropy
            encrypted_bytes = base64.b64decode(encrypted_b64)
            entropy_value = calculate_entropy(encrypted_bytes)

            log_to_csv("encryption", i, LABEL, metrics["cpu_percent"], metrics["memory_diff_mb"], 
                      metrics["time_diff_sec"], len(encrypted_bytes), entropy_value)

        # Convert base64 to bytes, then to hex string for storage
        encrypted_bytes = base64.b64decode(encrypted_result)
        hex_encrypted = encrypted_bytes.hex()
        
        target_cursor.execute("UPDATE data_store SET BLOWFISH_ENCRYPTION = %s WHERE file_size_label = %s;",
                              (hex_encrypted, LABEL))
        target_conn.commit()

      
    except Exception as e:
        print(f"[ERROR - BLOWFISH encryption] {e}")
        import traceback
        traceback.print_exc()
def decrypt_and_log_all(source_conn, source_cursor, target_conn, target_cursor):
    """Decrypt using hex storage approach"""
    try:
        source_cursor.execute("SELECT BLOWFISH_ENCRYPTION FROM data_store WHERE file_size_label = %s LIMIT 1;", (LABEL,))
        row = source_cursor.fetchone()
        if not row:
            print(f"[INFO] No BLOWFISH encrypted data found for label '{LABEL}'")
            return

        hex_encrypted = row[0]
        
        # Convert hex string back to bytes
        try:
            encrypted_text = bytes.fromhex(hex_encrypted)
          
        except ValueError as e:
            print(f"[ERROR] Failed to convert hex to bytes: {e}")
            return
        
        decrypted_result = None

        for i in range(1, TOTAL_ITERATIONS + 1):
            decrypted_result, metrics = BLOWFISH.decrypt(encrypted_text)
            # print(decrypted_result)  # Debugging output
            decrypted_size = len(decrypted_result.encode('utf-8'))

            log_to_csv("decryption", i, LABEL, metrics["cpu_percent"], metrics["memory_diff_mb"], 
                      metrics["time_diff_sec"], decrypted_size, 0)

        target_cursor.execute("UPDATE data_store SET BLOWFISH_DECRYPTION = %s WHERE file_size_label = %s;", 
                             (decrypted_result, LABEL))
        target_conn.commit()

        
    except Exception as e:
        print(f"[ERROR - BLOWFISH decryption] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    for try_number in range(1, TRY_NUMBER + 1):
        file_size = LABEL.replace(' ', '').replace('file', '').upper()  # '500KB'
        CSV_FILE = f"BLOWFISH_METRICS_{file_size}_{try_number}TRY_{TOTAL_ITERATIONS}loops.csv"

        init_csv()

        conn1 = conn2 = conn3 = None
        cur1 = cur2 = cur3 = None
        
        try:
            conn1 = psycopg2.connect(**grid_nodes[0])
            cur1 = conn1.cursor()

            conn2 = psycopg2.connect(**grid_nodes[1])
            cur2 = conn2.cursor()

            conn3 = psycopg2.connect(**grid_nodes[2])
            cur3 = conn3.cursor()

            encrypt_and_log_all(conn1, cur1, conn2, cur2)
            decrypt_and_log_all(conn2, cur2, conn3, cur3)

        except Exception as e:
            print(f"[ERROR - TRY {try_number}] {e}")
            import traceback
            traceback.print_exc()

        finally:
            connections = [(conn1, cur1), (conn2, cur2), (conn3, cur3)]
            for conn, cur in connections:
                try:
                    if cur:
                        cur.close()
                    if conn:
                        conn.close()
                except Exception as cleanup_error:
                    print(f"[WARNING] Error during cleanup: {cleanup_error}")

        print(f"[INFO] Completed TRY {try_number}\n")



# PostgreSQL Binary Data Storage Issue
# Problem Description
# When working with binary data (like encrypted content) in PostgreSQL databases, there's a common data type conversion issue that occurs between storage and retrieval operations.
# Root Cause

# Storage Process: When binary data is stored using psycopg2.Binary(), it gets properly converted to PostgreSQL's BYTEA data type
# Retrieval Process: However, when this data is retrieved from the database, PostgreSQL sometimes returns it as a string representation rather than actual bytes object
# Encryption Expectation: Cryptographic libraries (like PyCrypto's Blowfish) expect binary data as bytes objects, not strings

# Technical Details
# Error Manifestation
# When the string data is passed to the decryption function:
# pythoncipher.decrypt(string_data)  # Fails with "Object type <class 'str'> cannot be passed to C code"
# This happens because:

# The underlying C library expects raw binary data
# String representations cannot be processed by low-level cryptographic operations