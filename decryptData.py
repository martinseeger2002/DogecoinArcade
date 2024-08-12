import base58
import base64
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os

def load_private_key_from_wallet(wallet_path="./.smswallet.json"):
    with open(wallet_path, "r") as wallet_file:
        wallet_data = json.load(wallet_file)
        return wallet_data["privkey"]

def wif_to_hex(wif_key):
    decoded_wif = base58.b58decode_check(wif_key)
    privkey_hex = decoded_wif[1:-1] if len(decoded_wif) == 34 else decoded_wif[1:]
    return privkey_hex.hex()

def privkey_to_ec_privkey(wif_key):
    privkey_hex = wif_to_hex(wif_key)
    privkey_bytes = bytes.fromhex(privkey_hex)
    return ec.derive_private_key(int.from_bytes(privkey_bytes, "big"), ec.SECP256K1(), default_backend())

def decrypt_aes_key_with_privkey(privkey, encrypted_aes_key):
    temp_pubkey_bytes = encrypted_aes_key[:33]
    iv = encrypted_aes_key[33:45]
    ciphertext = encrypted_aes_key[45:-16]
    tag = encrypted_aes_key[-16:]

    temp_pubkey = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), temp_pubkey_bytes)
    shared_secret = privkey.exchange(ec.ECDH(), temp_pubkey)
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"ecdh derived key",
        backend=default_backend()
    ).derive(shared_secret)

    cipher = Cipher(algorithms.AES(derived_key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    aes_key = decryptor.update(ciphertext) + decryptor.finalize()

    return aes_key

def decrypt_data_with_aes(aes_key, encrypted_data):
    iv = encrypted_data[:12]
    tag = encrypted_data[-16:]
    ciphertext = encrypted_data[12:-16]
    
    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()

def decrypt_file(file_name, wallet_path="./.smswallet.json"):
    wif_key = load_private_key_from_wallet(wallet_path)
    privkey = privkey_to_ec_privkey(wif_key)

    input_file_path = os.path.join("./smscontent", file_name)
    output_file_path = os.path.join("./smsdecrypted", file_name)

    with open(input_file_path, "r") as f:
        encrypted_data_base64 = f.read().strip()

    encrypted_data = base64.b64decode(encrypted_data_base64)

    encrypted_aes_key = encrypted_data[:33+12+32+16]
    encrypted_data = encrypted_data[33+12+32+16:]

    aes_key = decrypt_aes_key_with_privkey(privkey, encrypted_aes_key)
    decrypted_data = decrypt_data_with_aes(aes_key, encrypted_data)

    os.makedirs("./smsdecrypted", exist_ok=True)
    with open(output_file_path, "wb") as f:
        f.write(decrypted_data)

    return output_file_path
