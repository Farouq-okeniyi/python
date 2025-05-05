# Encryption/blowfish_encryption.py
from Crypto.Cipher import Blowfish
import base64
from Crypto.Random import get_random_bytes

key = get_random_bytes(16)

def pad(text):
    while len(text) % 8 != 0:
        text += " "
    return text

def encrypt(data):
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    padded = pad(data)
    encrypted_bytes = cipher.encrypt(padded.encode())
    return encrypted_bytes  # return raw bytes

def decrypt(encrypted_bytes):
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    decrypted = cipher.decrypt(encrypted_bytes).decode().strip()
    return decrypted
