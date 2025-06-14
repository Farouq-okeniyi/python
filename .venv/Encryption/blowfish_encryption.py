from Crypto.Cipher import Blowfish
from Crypto.Random import get_random_bytes
import psutil
import time

key = get_random_bytes(16)

def pad(text):
    while len(text) % 8 != 0:
        text += " "
    return text

def get_nonzero_cpu_percent(max_attempts=3, fallback=1.0):
    for _ in range(max_attempts):
        cpu = psutil.cpu_percent(interval=0.05)
        if cpu != 0.0:
            return cpu
    return fallback

def encrypt(data):
    process = psutil.Process()
    before_mem = process.memory_info().rss / (1024 * 1024)

    psutil.cpu_percent(interval=None)  # Warm-up
    start_time = time.time()

    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    padded = pad(data)
    encrypted_bytes = cipher.encrypt(padded.encode())

    end_time = time.time()
    after_mem = process.memory_info().rss / (1024 * 1024)

    cpu_percent = get_nonzero_cpu_percent()

    metrics = {
        "cpu_percent": cpu_percent,
        "memory_diff_mb": after_mem - before_mem,
        "time_diff_sec": end_time - start_time
    }
    return encrypted_bytes, metrics

def decrypt(encrypted_bytes):
    process = psutil.Process()
    before_mem = process.memory_info().rss / (1024 * 1024)

    psutil.cpu_percent(interval=None)
    start_time = time.time()

    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    decrypted = cipher.decrypt(encrypted_bytes).decode().strip()

    end_time = time.time()
    after_mem = process.memory_info().rss / (1024 * 1024)
    cpu_percent = get_nonzero_cpu_percent()

    metrics = {
        "cpu_percent": cpu_percent,
        "memory_diff_mb": after_mem - before_mem,
        "time_diff_sec": end_time - start_time
    }

    return decrypted, metrics
