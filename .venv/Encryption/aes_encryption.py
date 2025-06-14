from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import psutil
import time
import os

key = b'Sixteen byte key'

def get_nonzero_cpu_percent(max_attempts=3, fallback=1.0):
    """
    Tries multiple times to get a non-zero CPU percent.
    Falls back to `fallback` if unsuccessful.
    """
    for _ in range(max_attempts):
        cpu = psutil.cpu_percent(interval=0.05)
        if cpu != 0.0:
            return cpu
    return fallback

def encrypt(plain_text: str) -> tuple[str, dict]:
    process = psutil.Process(os.getpid())
    before_mem = process.memory_info().rss / (1024 * 1024)

    psutil.cpu_percent(interval=None)  # Warm-up
    start_time = time.time()

    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plain_text.encode('utf-8'))
    encrypted_blob = cipher.nonce + tag + ciphertext
    encrypted_b64 = base64.b64encode(encrypted_blob).decode('utf-8')

    end_time = time.time()
    after_mem = process.memory_info().rss / (1024 * 1024)

    cpu_percent = get_nonzero_cpu_percent()

    metrics = {
        "cpu_percent": cpu_percent,
        "memory_diff_mb": after_mem - before_mem,
        "time_diff_sec": end_time - start_time
    }

    return encrypted_b64, metrics


def decrypt(encrypted_b64: str) -> tuple[str, dict]:
    encrypted_b64 = encrypted_b64.strip()
    encrypted_b64 += '=' * (-len(encrypted_b64) % 4)

    encrypted_blob = base64.b64decode(encrypted_b64)
    nonce = encrypted_blob[:16]
    tag = encrypted_blob[16:32]
    ciphertext = encrypted_blob[32:]

    process = psutil.Process(os.getpid())
    before_mem = process.memory_info().rss / (1024 * 1024)

    psutil.cpu_percent(interval=None)
    start_time = time.time()

    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    decrypted_bytes = cipher.decrypt_and_verify(ciphertext, tag)

    end_time = time.time()
    after_mem = process.memory_info().rss / (1024 * 1024)

    cpu_percent = get_nonzero_cpu_percent()

    metrics = {
        "cpu_percent": cpu_percent,
        "memory_diff_mb": after_mem - before_mem,
        "time_diff_sec": end_time - start_time
    }

    return decrypted_bytes.decode('utf-8'), metrics
