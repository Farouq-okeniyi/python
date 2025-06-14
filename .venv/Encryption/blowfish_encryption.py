# Encryption/blowfish_encryption.py
from Crypto.Cipher import Blowfish
import base64
from Crypto.Random import get_random_bytes
import psutil
import time

key = get_random_bytes(16)

def pad(text):
    while len(text) % 8 != 0:
        text += " "
    return text

def encrypt(data):
    before_cpu = psutil.cpu_percent(interval=0.0)
    before_mem = psutil.virtual_memory().used / (1024 * 1024)
    start_time = time.time()
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    padded = pad(data)
    encrypted_bytes = cipher.encrypt(padded.encode())
    end_time = time.time()
    after_cpu = psutil.cpu_percent(interval=0.0)
    after_mem = psutil.virtual_memory().used / (1024 * 1024)

    metrics = {
        "cpu_diff": after_cpu - before_cpu,
        "memory_diff_mb": after_mem - before_mem,
        "time_diff_sec": end_time - start_time
    }
    return encrypted_bytes, metrics  # return raw bytes

def decrypt(encrypted_bytes):
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    decrypted = cipher.decrypt(encrypted_bytes).decode().strip()
    return decrypted
