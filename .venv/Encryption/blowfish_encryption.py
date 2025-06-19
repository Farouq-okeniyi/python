from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import psutil
import time
import tracemalloc
from typing import Tuple

# ============ CONFIGURATION ============
KEY = b'myverysecurekey'  # Blowfish key: 4 to 56 bytes
BLOCK_SIZE = Blowfish.block_size  # Typically 8 bytes for Blowfish

# ============ HELPER FUNCTIONS ============

def get_nonzero_cpu_percent(max_attempts: int = 3, fallback: float = 1.0) -> float:
    """
    Measures CPU usage percentage, retries if 0.0 is returned.
    """
    for _ in range(max_attempts):
        cpu = psutil.cpu_percent(interval=0.05)
        if cpu != 0.0:
            return cpu
    return fallback


# ============ CORE FUNCTIONS ============

def encrypt(plaintext: str) -> Tuple[str, dict]:
    """
    Encrypts plaintext using Blowfish in ECB mode and returns base64 encoded ciphertext and metrics.
    
    Args:
        plaintext (str): The text to encrypt
    
    Returns:
        Tuple[str, dict]: Encrypted base64-encoded string and performance metrics
    """
    # Warm up CPU measurement
    psutil.cpu_percent(interval=None)
    
    # Start memory and time tracking
    tracemalloc.start()
    start_snapshot = tracemalloc.take_snapshot()
    start_time = time.perf_counter()
    
    try:
        cipher = Blowfish.new(KEY, Blowfish.MODE_ECB)
        padded_data = pad(plaintext.encode('utf-8'), BLOCK_SIZE)
        ciphertext = cipher.encrypt(padded_data)
        encrypted_b64 = base64.b64encode(ciphertext).decode('utf-8')

        # End tracking
        end_time = time.perf_counter()
        end_snapshot = tracemalloc.take_snapshot()
        
        # Calculate memory usage
        top_stats = end_snapshot.compare_to(start_snapshot, 'filename')
        total_bytes = sum(stat.size_diff for stat in top_stats)
        memory_used_mb = total_bytes / (1024 * 1024)
        
        tracemalloc.stop()

        metrics = {
            "cpu_percent": get_nonzero_cpu_percent(),
            "memory_diff_mb": memory_used_mb,
            "time_diff_sec": end_time - start_time
        }

        return encrypted_b64, metrics

    except Exception as e:
        tracemalloc.stop()
        raise Exception(f"Blowfish encryption failed: {str(e)}")


def decrypt(encrypted_input) -> Tuple[str, dict]:
    """
    Decrypts Blowfish-encrypted data and returns plaintext and metrics.
    
    Args:
        encrypted_input (Union[str, bytes]): Base64-encoded string or raw bytes to decrypt
    
    Returns:
        Tuple[str, dict]: Decrypted plaintext string and performance metrics
    """
    # Warm up CPU measurement
    psutil.cpu_percent(interval=None)
    
    # Start memory and time tracking
    tracemalloc.start()
    start_snapshot = tracemalloc.take_snapshot()
    start_time = time.perf_counter()

    try:
        # Handle input: either base64 string or bytes (e.g., from DB hex conversion)
        if isinstance(encrypted_input, str):
            encrypted_bytes = base64.b64decode(encrypted_input)
        elif isinstance(encrypted_input, (bytes, memoryview)):
            encrypted_bytes = encrypted_input if isinstance(encrypted_input, bytes) else encrypted_input.tobytes()
        else:
            raise TypeError("Unsupported encrypted input type")

        cipher = Blowfish.new(KEY, Blowfish.MODE_ECB)
        decrypted_padded = cipher.decrypt(encrypted_bytes)
        plaintext = unpad(decrypted_padded, BLOCK_SIZE).decode('utf-8')

        # End tracking
        end_time = time.perf_counter()
        end_snapshot = tracemalloc.take_snapshot()
        
        # Calculate memory usage
        top_stats = end_snapshot.compare_to(start_snapshot, 'filename')
        total_bytes = sum(stat.size_diff for stat in top_stats)
        memory_used_mb = total_bytes / (1024 * 1024)
        
        tracemalloc.stop()

        metrics = {
            "cpu_percent": get_nonzero_cpu_percent(),
            "memory_diff_mb": memory_used_mb,
            "time_diff_sec": end_time - start_time
        }

        return plaintext, metrics

    except Exception as e:
        tracemalloc.stop()
        raise Exception(f"Blowfish decryption failed: {str(e)}")

