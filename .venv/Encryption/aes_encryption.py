from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import psutil
import time

key = b'Sixteen byte key'

def encrypt(plain_text: str) -> tuple[str, dict]:
    before_cpu = psutil.cpu_percent(interval=0.0)
    before_mem = psutil.virtual_memory().used / (1024 * 1024)
    start_time = time.time()

    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plain_text.encode('utf-8'))
    encrypted_blob = cipher.nonce + tag + ciphertext
    encrypted_b64 = base64.b64encode(encrypted_blob).decode('utf-8')

    end_time = time.time()
    after_cpu = psutil.cpu_percent(interval=0.0)
    after_mem = psutil.virtual_memory().used / (1024 * 1024)

    metrics = {
        "cpu_diff": after_cpu - before_cpu,
        "memory_diff_mb": after_mem - before_mem,
        "time_diff_sec": end_time - start_time
    }

    return encrypted_b64, metrics


def decrypt(encrypted_b64: str) -> tuple[str, dict]:
    try:
        encrypted_b64 = encrypted_b64.strip()
        encrypted_b64 += '=' * (-len(encrypted_b64) % 4)

        encrypted_blob = base64.b64decode(encrypted_b64)
        nonce = encrypted_blob[:16]
        tag = encrypted_blob[16:32]
        ciphertext = encrypted_blob[32:]

        before_cpu = psutil.cpu_percent(interval=0.0)
        before_mem = psutil.virtual_memory().used / (1024 * 1024)
        start_time = time.time()

        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        decrypted_bytes = cipher.decrypt_and_verify(ciphertext, tag)

        end_time = time.time()
        after_cpu = psutil.cpu_percent(interval=0.0)
        after_mem = psutil.virtual_memory().used / (1024 * 1024)

        metrics = {
            "cpu_diff": after_cpu - before_cpu,
            "memory_diff_mb": after_mem - before_mem,
            "time_diff_sec": end_time - start_time
        }

        return decrypted_bytes.decode('utf-8'), metrics

    except Exception as e:
        print(f"[ERROR - decrypt_value] {e}")
        raise
