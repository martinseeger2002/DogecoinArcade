import base58
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def wif_to_hex(wif_key):
    # Decode the WIF key
    decoded_wif = base58.b58decode_check(wif_key)
    # The first byte is the network byte, and the last byte (optional) is the compression flag
    # The private key is the middle part
    privkey_hex = decoded_wif[1:-1] if len(decoded_wif) == 34 else decoded_wif[1:]
    return privkey_hex.hex()

def privkey_to_ec_privkey(wif_key):
    # Convert WIF to hexadecimal format
    privkey_hex = wif_to_hex(wif_key)

    # Convert the hexadecimal private key to an ECC private key object
    privkey_bytes = bytes.fromhex(privkey_hex)
    return ec.derive_private_key(int.from_bytes(privkey_bytes, "big"), ec.SECP256K1(), default_backend())

def decrypt_aes_key_with_privkey(privkey, encrypted_aes_key):
    # Extract the temporary public key, IV, encrypted AES key, and tag
    temp_pubkey_bytes = encrypted_aes_key[:33]
    iv = encrypted_aes_key[33:45]
    ciphertext = encrypted_aes_key[45:-16]
    tag = encrypted_aes_key[-16:]

    # Load the temporary public key
    temp_pubkey = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), temp_pubkey_bytes)

    # Derive the shared secret
    shared_secret = privkey.exchange(ec.ECDH(), temp_pubkey)

    # Derive the AES key using HKDF
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"ecdh derived key",
        backend=default_backend()
    ).derive(shared_secret)

    # Decrypt the AES key
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

def decrypt_data(wif_key, encrypted_data_base64):
    privkey = privkey_to_ec_privkey(wif_key)
    
    encrypted_data = base64.b64decode(encrypted_data_base64)
    
    # Assuming the first 33 + 12 + len(encrypted AES key) bytes are the encrypted AES key data
    encrypted_aes_key = encrypted_data[:33+12+32+16]  # Adjust this based on AES key size
    encrypted_data = encrypted_data[33+12+32+16:]  # Remaining part is the actual encrypted data
    
    # Decrypt the AES key with the private key
    aes_key = decrypt_aes_key_with_privkey(privkey, encrypted_aes_key)
    
    # Decrypt the data with the decrypted AES key
    decrypted_data = decrypt_data_with_aes(aes_key, encrypted_data)
    
    return decrypted_data

if __name__ == "__main__":
    # Always expecting a WIF key input
    wif_key = input("Enter the Bitcoin private key (WIF): ")
    
    # Encrypted data (base64)
    encrypted_data_base64 = input("Enter the encrypted data (base64): ")
    
    # Decrypt the data
    try:
        decrypted_data = decrypt_data(wif_key, encrypted_data_base64)
        print(f"Decrypted data: {decrypted_data.decode()}")
    except ValueError as e:
        print(f"Error: {e}")
