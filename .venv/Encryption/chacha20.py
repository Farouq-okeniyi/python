from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes
import base64
import psutil
import time

KEY = b'This_is_32_bytes_long_key_demo!!'  # 32 bytes
NONCE_SIZE = 12  # ChaCha20 requires 12-byte nonce

def get_nonzero_cpu_percent(max_attempts=3, fallback=1.0):
    for _ in range(max_attempts):
        cpu = psutil.cpu_percent(interval=0.05)
        if cpu != 0.0:
            return cpu
    return fallback

def encrypt(plaintext: str) -> tuple[str, dict]:
    process = psutil.Process()
    before_mem = process.memory_info().rss / (1024 * 1024)

    psutil.cpu_percent(interval=None)  # Warm up
    start_time = time.time()

    nonce = get_random_bytes(NONCE_SIZE)
    cipher = ChaCha20.new(key=KEY, nonce=nonce)
    ciphertext = cipher.encrypt(plaintext.encode('utf-8'))
    encrypted = base64.b64encode(nonce + ciphertext).decode('utf-8')

    end_time = time.time()
    after_mem = process.memory_info().rss / (1024 * 1024)
    cpu_percent = get_nonzero_cpu_percent()

    metrics = {
        "cpu_percent": cpu_percent,
        "memory_diff_mb": after_mem - before_mem,
        "time_diff_sec": end_time - start_time
    }
    return encrypted, metrics

def decrypt(encrypted: str) -> tuple[str, dict]:
    process = psutil.Process()
    before_mem = process.memory_info().rss / (1024 * 1024)

    psutil.cpu_percent(interval=None)
    start_time = time.time()

    decoded = base64.b64decode(encrypted.encode('utf-8'))
    nonce = decoded[:NONCE_SIZE]
    ciphertext = decoded[NONCE_SIZE:]
    cipher = ChaCha20.new(key=KEY, nonce=nonce)
    decrypted = cipher.decrypt(ciphertext).decode('utf-8')

    end_time = time.time()
    after_mem = process.memory_info().rss / (1024 * 1024)
    cpu_percent = get_nonzero_cpu_percent()

    metrics = {
        "cpu_percent": cpu_percent,
        "memory_diff_mb": after_mem - before_mem,
        "time_diff_sec": end_time - start_time
    }

    return decrypted, metrics
