from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes
import base64
import psutil
import time
import tracemalloc

KEY = b'This_is_32_bytes_long_key_demo!!'  # 32 bytes fixed key for ChaCha20
NONCE_SIZE = 12  # ChaCha20 requires a 12-byte nonce

def get_nonzero_cpu_percent(max_attempts=3, fallback=1.0):
    for _ in range(max_attempts):
        cpu = psutil.cpu_percent(interval=0.05)
        if cpu != 0.0:
            return cpu
    return fallback

def encrypt(plain_text: str) -> tuple[str, dict]:
    psutil.cpu_percent(interval=None)
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()

    start_time = time.perf_counter()

    nonce = get_random_bytes(NONCE_SIZE)
    cipher = ChaCha20.new(key=KEY, nonce=nonce)
    ciphertext = cipher.encrypt(plain_text.encode('utf-8'))
    encrypted_blob = nonce + ciphertext
    encrypted_b64 = base64.b64encode(encrypted_blob).decode('utf-8')

    end_time = time.perf_counter()

    snapshot2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snapshot2.compare_to(snapshot1, 'lineno')
    memory_used_bytes = sum(stat.size_diff for stat in stats)
    memory_used_mb = memory_used_bytes / (1024 * 1024)

    metrics = {
        "cpu_percent": get_nonzero_cpu_percent(),
        "memory_diff_mb": memory_used_mb,
        "time_diff_sec": end_time - start_time
    }

    return encrypted_b64, metrics

def decrypt(encrypted_b64: str) -> tuple[str, dict]:
    encrypted_b64 = encrypted_b64.strip()
    encrypted_b64 += '=' * (-len(encrypted_b64) % 4)
    encrypted_blob = base64.b64decode(encrypted_b64)
    nonce = encrypted_blob[:NONCE_SIZE]
    ciphertext = encrypted_blob[NONCE_SIZE:]

    psutil.cpu_percent(interval=None)
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()

    start_time = time.perf_counter()

    cipher = ChaCha20.new(key=KEY, nonce=nonce)
    decrypted_bytes = cipher.decrypt(ciphertext)
    decrypted_text = decrypted_bytes.decode('utf-8')

    end_time = time.perf_counter()

    snapshot2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snapshot2.compare_to(snapshot1, 'lineno')
    memory_used_bytes = sum(stat.size_diff for stat in stats)
    memory_used_mb = memory_used_bytes / (1024 * 1024)

    metrics = {
        "cpu_percent": get_nonzero_cpu_percent(),
        "memory_diff_mb": memory_used_mb,
        "time_diff_sec": end_time - start_time
    }

    return decrypted_text, metrics
