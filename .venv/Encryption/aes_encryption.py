from Crypto.PublicKey import ECC
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import HKDF
import base64
import json
import psutil
import time
import tracemalloc

# Load ECC key pair
with open("ecc_private.pem", "rt") as f:
    private_key = ECC.import_key(f.read())

with open("ecc_public.pem", "rt") as f:
    public_key = ECC.import_key(f.read())

def get_nonzero_cpu_percent(max_attempts=3, fallback=1.0):
    for _ in range(max_attempts):
        cpu = psutil.cpu_percent(interval=0.05)
        if cpu != 0.0:
            return cpu
    return fallback

def encrypt(data: str) -> tuple[str, dict]:
    psutil.cpu_percent(interval=None)
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()

    start_time = time.perf_counter()

    ephemeral_key = ECC.generate(curve='P-256')
    shared_secret = ephemeral_key.d * public_key.pointQ
    shared_secret_bytes = int(shared_secret.x).to_bytes(32, byteorder='big')
    sym_key = HKDF(shared_secret_bytes, 16, b'', SHA256)

    cipher = AES.new(sym_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))

    encrypted_package = {
        'ciphertext': base64.b64encode(ciphertext).decode(),
        'nonce': base64.b64encode(cipher.nonce).decode(),
        'tag': base64.b64encode(tag).decode(),
        'ephemeral_pubkey': ephemeral_key.public_key().export_key(format='PEM')
    }

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

    return json.dumps(encrypted_package), metrics

def decrypt(encrypted_json: str) -> tuple[str, dict]:
    psutil.cpu_percent(interval=None)
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()

    start_time = time.perf_counter()

    data = json.loads(encrypted_json)
    ephemeral_pubkey = ECC.import_key(data['ephemeral_pubkey'])
    shared_secret = private_key.d * ephemeral_pubkey.pointQ
    shared_secret_bytes = int(shared_secret.x).to_bytes(32, byteorder='big')
    sym_key = HKDF(shared_secret_bytes, 16, b'', SHA256)

    cipher = AES.new(sym_key, AES.MODE_EAX, nonce=base64.b64decode(data['nonce']))
    plaintext = cipher.decrypt_and_verify(
        base64.b64decode(data['ciphertext']),
        base64.b64decode(data['tag'])
    )

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

    return plaintext.decode('utf-8'), metrics
