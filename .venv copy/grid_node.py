import psycopg2
import importlib
import base64
import time
import psutil
from prometheus_client import start_http_server, Summary, Gauge, Counter

# ========== Configuration ==========

# Start Prometheus HTTP server
start_http_server(8000)
print("Prometheus server running on port 8000...")
#hello

#hi
# Prometheus Metrics
REQUEST_TIME = Summary('encryption_request_processing_seconds', 'Time spent processing encryption per request')
CPU_USAGE = Gauge('encryption_cpu_usage_percent', 'CPU usage percentage during encryption')
MEMORY_USAGE = Gauge('encryption_memory_usage_mb', 'Memory usage (MB) during encryption')
BYTES_ENCRYPTED = Counter('encryption_bytes_total', 'Total number of bytes encrypted')
ENCRYPTION_OPERATIONS = Counter('encryption_operations_total', 'Total encryption operations performed')
ENCRYPTION_FAILURES = Counter('encryption_failures_total', 'Total failed encryption operations')
KEY_ROTATIONS = Counter('encryption_key_rotations_total', 'Total number of encryption key rotations')
KEY_EXPIRY_SECONDS = Gauge('encryption_key_expiry_seconds_remaining', 'Seconds remaining before key expires')
ENCRYPTION_QUEUE_LENGTH = Gauge('encryption_queue_length', 'Current encryption queue size')
CURRENT_ENCRYPTIONS = Gauge('current_   encryption_sessions', 'Concurrent encryption operations')


# Select Encryption Algorithm Module (change this easily)
encryption_module = importlib.import_module("Encryption.aes_encryption")
# Example modules: Encryption.aes_encryption, Encryption.blowfish_encryption, Encryption.rsa_encryption, Encryption.ecc_encryption

# Database (Grid Nodes)
grid_nodes = [
    {"dbname": "grid_node_1", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_2", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
    {"dbname": "grid_node_3", "user": "postgres", "password": "panda020704", "host": "localhost", "port": 5433},
]

# ========== Functions ==========

def get_system_usage():
    CPU_USAGE.set(psutil.cpu_percent(interval=1))  # CPU percentage
    MEMORY_USAGE.set(psutil.virtual_memory().used / (1024 * 1024))  # RAM used in MB

# Encrypt process for a node
def encrypt_data(raw_data):
    @REQUEST_TIME.time()
    def process():
        # Encrypt multiple times to simulate heavier load
        for _ in range(1000):
            encrypted = encryption_module.encrypt(raw_data)
        return encrypted

    return process()

# ========== Main Monitoring Loop ==========
i=0
while i<=1000:
    for node in grid_nodes:
        try:
            print(f"\nConnecting to {node['dbname']}...")
            conn = psycopg2.connect(**node)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM data_store;")
            rows = cursor.fetchall()

            print(f"Data from {node['dbname']}:")
            for row in rows:
                raw = str(row)

                # Monitor system usage
                get_system_usage()

                # Encrypt the data
                encrypted = encrypt_data(raw)

                # Optional: you can decrypt also if you want
                # decrypted = encryption_module.decrypt(encrypted)

                print(f"Original: {raw}")
                print(f"Encrypted (short): {str(encrypted)[:30]}...\n")
                i = i+1
            cursor.close()
            conn.close()
        
            
        
        except Exception as e:
            print(f"Failed to connect to {node['dbname']}: {e}")

    # Sleep a little to not overload Prometheus
    time.sleep(5)

