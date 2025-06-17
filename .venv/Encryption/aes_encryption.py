from Crypto.Cipher import AES
import base64
import psutil
import time
import tracemalloc

key = b'Sixteen byte key'  # 16 bytes = 128-bit key

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

    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plain_text.encode('utf-8'))
    encrypted_blob = cipher.nonce + tag + ciphertext
    encrypted_b64 = base64.b64encode(encrypted_blob).decode('utf-8')

    end_time = time.perf_counter()

    snapshot2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    # Calculate actual memory used during encryption
    stats = snapshot2.compare_to(snapshot1, 'lineno')
    memory_used_bytes = sum([stat.size_diff for stat in stats])
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
    nonce = encrypted_blob[:16]
    tag = encrypted_blob[16:32]
    ciphertext = encrypted_blob[32:]

    psutil.cpu_percent(interval=None)
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()

    start_time = time.perf_counter()

    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    decrypted_bytes = cipher.decrypt_and_verify(ciphertext, tag)
    decrypted_text = decrypted_bytes.decode('utf-8')

    end_time = time.perf_counter()

    snapshot2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    # Calculate actual memory used during decryption
    stats = snapshot2.compare_to(snapshot1, 'lineno')
    memory_used_bytes = sum([stat.size_diff for stat in stats])
    memory_used_mb = memory_used_bytes / (1024 * 1024)

    metrics = {
        "cpu_percent": get_nonzero_cpu_percent(),
        "memory_diff_mb": memory_used_mb,
        "time_diff_sec": end_time - start_time
    }

    return decrypted_text, metrics
