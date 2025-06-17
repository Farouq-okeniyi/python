from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import pad, unpad
import psutil
import time

KEY = b'myverysecurekey'  # 4-56 bytes
BLOCK_SIZE = 8            # Blowfish block size

def encrypt(plaintext: str):
    cipher = Blowfish.new(KEY, Blowfish.MODE_ECB)
    plaintext_bytes = plaintext.encode('utf-8')
    padded_data = pad(plaintext_bytes, BLOCK_SIZE)

    start = time.perf_counter()
    cpu_before = psutil.cpu_percent()
    memory_before = psutil.virtual_memory().used / (1024 * 1024)

    ciphertext = cipher.encrypt(padded_data)

    cpu_after = psutil.cpu_percent()
    memory_after = psutil.virtual_memory().used / (1024 * 1024)
    end = time.perf_counter()

    metrics = {
        "cpu_percent": cpu_after,
        "memory_diff_mb": memory_after - memory_before,
        "time_diff_sec": end - start
    }

    return ciphertext, metrics
def decrypt(ciphertext: bytes):
    if isinstance(ciphertext, memoryview):  # PostgreSQL might return memoryview
        ciphertext = ciphertext.tobytes()

    cipher = Blowfish.new(KEY, Blowfish.MODE_ECB)

    start = time.perf_counter()
    cpu_before = psutil.cpu_percent()
    memory_before = psutil.virtual_memory().used / (1024 * 1024)

    decrypted_padded = cipher.decrypt(ciphertext)
    plaintext_bytes = unpad(decrypted_padded, BLOCK_SIZE)
    plaintext = plaintext_bytes.decode('utf-8')

    cpu_after = psutil.cpu_percent()
    memory_after = psutil.virtual_memory().used / (1024 * 1024)
    end = time.perf_counter()

    metrics = {
        "cpu_percent": cpu_after,
        "memory_diff_mb": memory_after - memory_before,
        "time_diff_sec": end - start
    }

    return plaintext, metrics
