from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

# Use a fixed key for demo; in real use, store and load securely
key = b'Sixteen byte key'  # note the leading 'b' for bytes


def encrypt(plain_text: str) -> str:
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plain_text.encode('utf-8'))
    encrypted_blob = cipher.nonce + tag + ciphertext
    encrypted_b64 = base64.b64encode(encrypted_blob).decode('utf-8')
    return encrypted_b64

def decrypt(encrypted_b64: str) -> str:
    try:
        encrypted_b64 = encrypted_b64.strip()

        # Add padding if missing
        encrypted_b64 += '=' * (-len(encrypted_b64) % 4)

        encrypted_blob = base64.b64decode(encrypted_b64)
        nonce = encrypted_blob[:16]
        tag = encrypted_blob[16:32]
        ciphertext = encrypted_blob[32:]

        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        decrypted_bytes = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"[ERROR - decrypt_value] {e}")
        raise
