from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes
import base64
import psutil
import time
import tracemalloc
from typing import Tuple

# Fixed 32-byte key for ChaCha20
KEY = b'This_is_32_bytes_long_key_demo!!'  # 32 bytes
NONCE_SIZE = 12  # ChaCha20 requires 12-byte nonce


def get_nonzero_cpu_percent(max_attempts: int = 3, fallback: float = 1.0) -> float:
    """
    Measures CPU usage percentage, retries if 0.0 is returned.
    """
    for _ in range(max_attempts):
        cpu = psutil.cpu_percent(interval=0.05)
        if cpu != 0.0:
            return cpu
    return fallback


def encrypt(plaintext: str) -> Tuple[str, dict]:
    """
    Encrypts the plaintext using ChaCha20 and returns encrypted data and standard metrics.
    
    Args:
        plaintext (str): The text to encrypt
        
    Returns:
        Tuple[str, dict]: Encrypted text (base64 encoded) and metrics dictionary
    """
    # Warm up CPU measurement
    psutil.cpu_percent(interval=None)
    
    # Start memory and time tracking
    tracemalloc.start()
    start_snapshot = tracemalloc.take_snapshot()
    start_time = time.perf_counter()

    try:
        # Generate random nonce
        nonce = get_random_bytes(NONCE_SIZE)
        
        # Create cipher and encrypt
        cipher = ChaCha20.new(key=KEY, nonce=nonce)
        ciphertext = cipher.encrypt(plaintext.encode('utf-8'))
        
        # Combine nonce + ciphertext and encode to base64
        encrypted = base64.b64encode(nonce + ciphertext).decode('utf-8')

        # End tracking
        end_time = time.perf_counter()
        end_snapshot = tracemalloc.take_snapshot()
        
        # Calculate memory difference
        top_stats = end_snapshot.compare_to(start_snapshot, 'filename')
        total_bytes = sum(stat.size_diff for stat in top_stats)
        memory_used_mb = total_bytes / (1024 * 1024)
        
        tracemalloc.stop()

        # Get CPU usage
        cpu_percent = get_nonzero_cpu_percent()

        metrics = {
            "cpu_percent": cpu_percent,
            "memory_diff_mb": memory_used_mb,
            "time_diff_sec": end_time - start_time
        }

        return encrypted, metrics

    except Exception as e:
        tracemalloc.stop()
        raise Exception(f"ChaCha20 encryption failed: {str(e)}")


def decrypt(encrypted: str) -> Tuple[str, dict]:
    """
    Decrypts a ChaCha20 encrypted string and returns plaintext and standard metrics.
    
    Args:
        encrypted (str): Base64 encoded encrypted text
        
    Returns:
        Tuple[str, dict]: Decrypted plaintext and metrics dictionary
    """
    # Warm up CPU measurement
    psutil.cpu_percent(interval=None)
    
    # Start memory and time tracking
    tracemalloc.start()
    start_snapshot = tracemalloc.take_snapshot()
    start_time = time.perf_counter()

    try:
        # Decode from base64
        decoded = base64.b64decode(encrypted.encode('utf-8'))
        
        # Extract nonce and ciphertext
        nonce = decoded[:NONCE_SIZE]
        ciphertext = decoded[NONCE_SIZE:]
        
        # Create cipher and decrypt
        cipher = ChaCha20.new(key=KEY, nonce=nonce)
        decrypted = cipher.decrypt(ciphertext).decode('utf-8')

        # End tracking
        end_time = time.perf_counter()
        end_snapshot = tracemalloc.take_snapshot()
        
        # Calculate memory difference
        top_stats = end_snapshot.compare_to(start_snapshot, 'filename')
        total_bytes = sum(stat.size_diff for stat in top_stats)
        memory_used_mb = total_bytes / (1024 * 1024)
        
        tracemalloc.stop()

        # Get CPU usage
        cpu_percent = get_nonzero_cpu_percent()

        metrics = {
            "cpu_percent": cpu_percent,
            "memory_diff_mb": memory_used_mb,
            "time_diff_sec": end_time - start_time
        }

        return decrypted, metrics

    except Exception as e:
        tracemalloc.stop()
        raise Exception(f"ChaCha20 decryption failed: {str(e)}")