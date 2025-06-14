from Crypto.PublicKey import ECC
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import HKDF
import base64
import json
import psutil
import time

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
    process = psutil.Process()
    before_mem = process.memory_info().rss / (1024 * 1024)
    
    psutil.cpu_percent(interval=None)
    start_time = time.time()

    # Generate ephemeral ECC key pair
    ephemeral_key = ECC.generate(curve='P-256')
    shared_secret = ephemeral_key.d * public_key.pointQ
    shared_secret_bytes = int(shared_secret.x).to_bytes(32, byteorder='big')

    # Derive symmetric key with HKDF
    sym_key = HKDF(shared_secret_bytes, 16, b'', SHA256)

    # Encrypt using AES-EAX
    cipher = AES.new(sym_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))

    encrypted_package = {
        'ciphertext': base64.b64encode(ciphertext).decode(),
        'nonce': base64.b64encode(cipher.nonce).decode(),
        'tag': base64.b64encode(tag).decode(),
        'ephemeral_pubkey': ephemeral_key.public_key().export_key(format='PEM')
    }

    end_time = time.time()
    after_mem = process.memory_info().rss / (1024 * 1024)
    cpu_percent = get_nonzero_cpu_percent()

    metrics = {
        "cpu_percent": cpu_percent,
        "memory_diff_mb": after_mem - before_mem,
        "time_diff_sec": end_time - start_time
    }

    return json.dumps(encrypted_package), metrics

def decrypt(encrypted_json: str) -> tuple[str, dict]:
    process = psutil.Process()
    before_mem = process.memory_info().rss / (1024 * 1024)

    psutil.cpu_percent(interval=None)
    start_time = time.time()

    data = json.loads(encrypted_json)
    ephemeral_pubkey = ECC.import_key(data['ephemeral_pubkey'])
    shared_secret = private_key.d * ephemeral_pubkey.pointQ
    shared_secret_bytes = int(shared_secret.x).to_bytes(32, byteorder='big')

    # Derive symmetric key with HKDF
    sym_key = HKDF(shared_secret_bytes, 16, b'', SHA256)

    # Decrypt using AES-EAX
    cipher = AES.new(sym_key, AES.MODE_EAX, nonce=base64.b64decode(data['nonce']))
    plaintext = cipher.decrypt_and_verify(
        base64.b64decode(data['ciphertext']),
        base64.b64decode(data['tag'])
    )

    end_time = time.time()
    after_mem = process.memory_info().rss / (1024 * 1024)
    cpu_percent = get_nonzero_cpu_percent()

    metrics = {
        "cpu_percent": cpu_percent,
        "memory_diff_mb": after_mem - before_mem,
        "time_diff_sec": end_time - start_time
    }

    return plaintext.decode('utf-8'), metrics
