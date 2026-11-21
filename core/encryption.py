"""
encryption.py
Handles all encryption and decryption of vault data.
Uses AES-GCM for authenticated encryption and PBKDF2 for key derivation.
"""

import os
import json
import base64
import hashlib

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PBKDF2_ITERATIONS = 600_000   # NIST recommended minimum (2023)
KEY_LENGTH        = 32        # 256 bits
SALT_LENGTH       = 32        # 256 bits
NONCE_LENGTH      = 12        # 96 bits — standard for AES-GCM

# Derive a symmetric key from the given password and salt.
def derive_key(master_password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,)
    return kdf.derive(master_password.encode('utf-8'))

# Generate a cryptographically random 32-byte salt
def generate_salt() -> bytes:
    return os.urandom(SALT_LENGTH)

# Convert salt bytes to a base64-encoded string for storage
def salt_to_string(salt: bytes) -> str:
    return base64.b64encode(salt).decode('utf-8')

# Convert a base64-encoded string back to salt bytes
def string_to_salt(salt_string: str) -> bytes:
    return base64.b64decode(salt_string.encode('utf-8'))

# Encrypt the given plaintext using AES-GCM with a key derived from the master password and salt.
def encrypt(data: dict, Dkey: bytes) -> bytes:
    plaintext=json.dumps(data).encode('utf-8')
    nonce=os.urandom(NONCE_LENGTH)
    ciphertext=AESGCM(Dkey).encrypt(nonce,plaintext,None)

    return nonce + ciphertext

# Decrypt the given ciphertext using AES-GCM with a key derived from the master password and salt.
def decrypt(lock: bytes, Dkey: bytes) -> dict:
    nonce = lock[:NONCE_LENGTH]
    ciphertext = lock[NONCE_LENGTH:]
    plaintext = AESGCM(Dkey).decrypt(nonce, ciphertext, None)

    return json.loads(plaintext.decode('utf-8'))

# Verify that the provided master password is correct by attempting to decrypt the lock.
def verify_master_password(master_password: str, salt: bytes, lock: bytes) -> bool:
    try:
        Trial_Dkey = derive_key(master_password, salt)
        decrypt(lock, Trial_Dkey)
        return True
    except:
        return False
    

#  Quick test 

if __name__ == "__main__":
    print("Testing encryption module...")

    # 1. Generate a salt
    salt = generate_salt()
    print(f"Salt generated: {len(salt)} bytes")
    print(f"salt in bytes: {salt}")
    print(f"Salt as string: {salt_to_string(salt)}")

    # 2. Derive a key from a test master password
    key = derive_key("MyTestPassword123!", salt)
    print(f"Key derived: {len(key)} bytes")
    print(f"Key in bytes: {key}")

    # 3. Encrypt some dummy vault data
    dummy_data = {
        "entries": [
            {"title": "Test", "username": "user@test.com", "password": "secret"}
        ]
    }
    encrypted = encrypt(dummy_data, key)
    print(f"Encrypted: {len(encrypted)} bytes")
    print(f" encrypt: {encrypted}")

    # 4. Decrypt it back
    decrypted = decrypt(encrypted, key)
    print(f"Decrypted title: {decrypted['entries'][0]['title']}")

    # 5. Test wrong password is rejected
    wrong_key = derive_key("WrongPassword!", salt)
    result = verify_master_password("WrongPassword!", salt, encrypted)
    print(f"Wrong password rejected: {not result}")

    print("All tests passed!")