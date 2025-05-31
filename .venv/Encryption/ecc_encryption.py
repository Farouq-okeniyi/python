from Crypto.PublicKey import ECC
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import HKDF
import base64
import json

# Generate ECC key pair
from Crypto.PublicKey import ECC

with open("ecc_private.pem", "rt") as f:
    private_key = ECC.import_key(f.read())

with open("ecc_public.pem", "rt") as f:
    public_key = ECC.import_key(f.read())

def encrypt(data: str):
    # Generate ephemeral ECC key pair
    ephemeral_key = ECC.generate(curve='P-256')
    shared_secret = ephemeral_key.d * public_key.pointQ

    # Derive a symmetric key using HKDF
    shared_secret_bytes = int(shared_secret.x).to_bytes(32, byteorder='big')
    sym_key = HKDF(shared_secret_bytes, 16, b'', SHA256)

    # Encrypt the data using AES
    cipher = AES.new(sym_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))

    encrypted_package = {
        'ciphertext': base64.b64encode(ciphertext).decode(),
        'nonce': base64.b64encode(cipher.nonce).decode(),
        'tag': base64.b64encode(tag).decode(),
        'ephemeral_pubkey': ephemeral_key.public_key().export_key(format='PEM')
    }

    return json.dumps(encrypted_package)

def decrypt(encrypted_json: str):
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

    return plaintext.decode('utf-8')
