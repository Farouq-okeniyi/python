from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes
import base64

# ✅ Fixed 32-byte key
KEY = b'This_is_32_bytes_long_key_demo!!'  # 32 bytes
NONCE_SIZE = 12  # ChaCha20 requires 12-byte nonce

def encrypt(plaintext: str) -> str:
    nonce = get_random_bytes(NONCE_SIZE)
    cipher = ChaCha20.new(key=KEY, nonce=nonce)
    ciphertext = cipher.encrypt(plaintext.encode('utf-8'))
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def decrypt(encrypted: str) -> str:
    decoded = base64.b64decode(encrypted.encode('utf-8'))
    nonce = decoded[:NONCE_SIZE]
    ciphertext = decoded[NONCE_SIZE:]
    cipher = ChaCha20.new(key=KEY, nonce=nonce)
    return cipher.decrypt(ciphertext).decode('utf-8')
