import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization  # Added serialization import
from cryptography.hazmat.backends import default_backend

def pubkey_to_ec_point(pubkey_hex):
    pubkey_bytes = bytes.fromhex(pubkey_hex)
    return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), pubkey_bytes)

def generate_aes_key():
    return os.urandom(32)  # AES-256

def encrypt_aes_key_with_pubkey(pubkey, aes_key):
    # Generate a temporary private key for ECDH
    temp_privkey = ec.generate_private_key(ec.SECP256K1(), default_backend())
    shared_secret = temp_privkey.exchange(ec.ECDH(), pubkey)

    # Derive a key from the shared secret
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"ecdh derived key",
        backend=default_backend()
    ).derive(shared_secret)

    # Encrypt the AES key using the derived key
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(derived_key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_aes_key = encryptor.update(aes_key) + encryptor.finalize()

    # Return the temporary public key, IV, encrypted AES key, and tag
    temp_pubkey = temp_privkey.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint
    )
    return temp_pubkey + iv + encrypted_aes_key + encryptor.tag

def encrypt_data_with_aes(aes_key, data):
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return iv + ciphertext + encryptor.tag

def encrypt_data(pubkey_hex, data):
    pubkey = pubkey_to_ec_point(pubkey_hex)
    
    # Generate AES key
    aes_key = generate_aes_key()
    
    # Encrypt the AES key with the public key using ECDH
    encrypted_aes_key = encrypt_aes_key_with_pubkey(pubkey, aes_key)
    
    # Encrypt the data with AES
    encrypted_data = encrypt_data_with_aes(aes_key, data)
    
    # Combine the encrypted AES key and the encrypted data
    return base64.b64encode(encrypted_aes_key + encrypted_data)

if __name__ == "__main__":
    # Sample Bitcoin public key (in hex)
    pubkey_hex = input("Enter the Bitcoin public key (hex): ")
    
    # Data to encrypt
    data = input("Enter the data to encrypt: ").encode()
    
    # Encrypt the data
    encrypted_data = encrypt_data(pubkey_hex, data)
    print(f"Encrypted data: {encrypted_data.decode()}")
