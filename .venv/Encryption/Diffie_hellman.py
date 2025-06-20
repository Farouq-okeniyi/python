import secrets
import time
import psutil
import tracemalloc
from hashlib import sha256
from Crypto.Cipher import AES
import base64

# Example prime and generator (small for demonstration only)
P = 23
G = 5

def get_nonzero_cpu_percent(max_attempts=3, fallback=1.0):
    for _ in range(max_attempts):
        cpu = psutil.cpu_percent(interval=0.05)
        if cpu != 0.0:
            return cpu
    return fallback

def generate_private_key(p: int) -> int:
    return secrets.randbelow(p-2) + 2

def generate_public_key(private_key: int, g: int, p: int) -> int:
    return pow(g, private_key, p)

def compute_shared_secret(their_public: int, my_private: int, p: int) -> bytes:
    shared_secret = pow(their_public, my_private, p)
    return sha256(str(shared_secret).encode()).digest()  # Derive 256-bit AES key

def encrypt(plaintext: str, key: bytes) -> tuple[str, dict]:
    psutil.cpu_percent(interval=None)
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()

    start_time = time.perf_counter()

    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
    encrypted_blob = cipher.nonce + tag + ciphertext
    encrypted_b64 = base64.b64encode(encrypted_blob).decode('utf-8')

    end_time = time.perf_counter()
    snapshot2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snapshot2.compare_to(snapshot1, 'lineno')
    memory_used_bytes = sum(stat.size_diff for stat in stats)
    memory_used_mb = memory_used_bytes / (1024 * 1024)

    return encrypted_b64, {
        "cpu_percent": get_nonzero_cpu_percent(),
        "memory_diff_mb": memory_used_mb,
        "time_diff_sec": end_time - start_time
    }

def decrypt(encrypted_b64: str, key: bytes) -> tuple[str, dict]:
    psutil.cpu_percent(interval=None)
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()

    start_time = time.perf_counter()

    encrypted_blob = base64.b64decode(encrypted_b64)
    nonce = encrypted_blob[:16]
    tag = encrypted_blob[16:32]
    ciphertext = encrypted_blob[32:]

    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    decrypted = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')

    end_time = time.perf_counter()
    snapshot2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snapshot2.compare_to(snapshot1, 'lineno')
    memory_used_bytes = sum(stat.size_diff for stat in stats)
    memory_used_mb = memory_used_bytes / (1024 * 1024)

    return decrypted, {
        "cpu_percent": get_nonzero_cpu_percent(),
        "memory_diff_mb": memory_used_mb,
        "time_diff_sec": end_time - start_time
    }

if __name__ == "__main__":
    # Generate private/public keys for A and B
    a_private = generate_private_key(P)
    a_public = generate_public_key(a_private, G, P)

    b_private = generate_private_key(P)
    b_public = generate_public_key(b_private, G, P)

    # Compute shared secret (symmetric AES key)
    key_a = compute_shared_secret(b_public, a_private, P)
    key_b = compute_shared_secret(a_public, b_private, P)
    assert key_a == key_b, "Shared secrets do not match"

    shared_key = key_a

    # Encrypt and decrypt a sample message
    plaintext = "This is a secret message using Diffie-Hellman!"
    encrypted, encrypt_metrics = encrypt(plaintext, shared_key)
    decrypted, decrypt_metrics = decrypt(encrypted, shared_key)

    # Results
