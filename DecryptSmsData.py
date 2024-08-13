import base58
import base64
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os
import mimetypes

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

def decrypt_file(txid, wallet_path="./.smswallet.json"):
    # Load private key from wallet
    wif_key = load_private_key_from_wallet(wallet_path)
    privkey = privkey_to_ec_privkey(wif_key)

    # Locate the corresponding JSON file in the /smscontent directory
    input_file_path = os.path.join("./smscontent", f"{txid}.json")

    if not os.path.exists(input_file_path):
        print(f"No file found for transaction ID: {txid}")
        return

    # Load the JSON content
    with open(input_file_path, "r") as json_file:
        sms_data = json.load(json_file)

    encrypted_data_base64 = sms_data['encrypted_data']
    mimetype = sms_data['mimetype']

    # Decode the encrypted data
    encrypted_data = base64.b64decode(encrypted_data_base64)
    encrypted_aes_key = encrypted_data[:33+12+32+16]
    encrypted_message = encrypted_data[33+12+32+16:]

    # Decrypt the AES key and the data
    aes_key = decrypt_aes_key_with_privkey(privkey, encrypted_aes_key)
    decrypted_data = decrypt_data_with_aes(aes_key, encrypted_message)

    # For non-text files, the decrypted data is still base64-encoded, so decode it
    if mimetype != "text/plain":
        decrypted_data = base64.b64decode(decrypted_data)

    # Determine the output file path based on the MIME type, all in one output directory
    output_dir = "./decryptedsmscontent"
    os.makedirs(output_dir, exist_ok=True)

    if mimetype == "text/plain":
        output_file_path = os.path.join(output_dir, f"{txid}.txt")
        with open(output_file_path, "w") as file:
            file.write(decrypted_data.decode())
        print(f"Decrypted text saved to {output_file_path}")
    else:
        # Handle specific cases and fall back to guessing the extension using mimetypes module
        extension = None
        if mimetype == "image/webp":
            extension = ".webp"
        elif mimetype == "image/jpeg":
            extension = ".jpg"
        elif mimetype == "image/png":
            extension = ".png"
        else:
            extension = mimetypes.guess_extension(mimetype) or ""

        if extension:
            output_file_path = os.path.join(output_dir, f"{txid}{extension}")
            with open(output_file_path, "wb") as file:
                file.write(decrypted_data)
            print(f"Decrypted file saved to {output_file_path}")
        else:
            print(f"Unhandled MIME type: {mimetype}, could not determine a valid extension.")

def main():
    # Prompt for transaction ID
    txid = input("Enter the transaction ID: ")
    decrypt_file(txid)

if __name__ == "__main__":
    main()
