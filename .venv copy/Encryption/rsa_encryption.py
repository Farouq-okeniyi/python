from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

key = RSA.generate(2048)
public_key = key.publickey()
cipher_rsa = PKCS1_OAEP.new(public_key)

def encrypt(data):
    return base64.b64encode(cipher_rsa.encrypt(data.encode())).decode()

def decrypt(data):
    cipher = PKCS1_OAEP.new(key)
    return cipher.decrypt(base64.b64decode(data)).decode()
