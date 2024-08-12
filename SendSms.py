import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import subprocess
import datetime
import json

def pubkey_to_ec_point(pubkey_hex):
    pubkey_bytes = bytes.fromhex(pubkey_hex)
    return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), pubkey_bytes)

def generate_aes_key():
    return os.urandom(32)  # AES-256

def encrypt_aes_key_with_pubkey(pubkey, aes_key):
    temp_privkey = ec.generate_private_key(ec.SECP256K1(), default_backend())
    shared_secret = temp_privkey.exchange(ec.ECDH(), pubkey)

    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"ecdh derived key",
        backend=default_backend()
    ).derive(shared_secret)

    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(derived_key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_aes_key = encryptor.update(aes_key) + encryptor.finalize()

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
    aes_key = generate_aes_key()
    encrypted_aes_key = encrypt_aes_key_with_pubkey(pubkey, aes_key)
    encrypted_data = encrypt_data_with_aes(aes_key, data)
    return base64.b64encode(encrypted_aes_key + encrypted_data)

def save_encrypted_data(encrypted_data, filepath):
    with open(filepath, 'w') as file:
        file.write(encrypted_data.decode())  # Save only the encrypted data
    print(f"Encrypted data saved to {filepath}")

def mint_sms(wallet_address, filepath):
    try:
        result = subprocess.run(['node', '.', 'sms', wallet_address, filepath], 
                                capture_output=True, text=True, check=True)
        if result.returncode == 0:
            output_lines = result.stdout.strip().splitlines()
            # Assuming the txid is always in the last line of the output
            txid_line = output_lines[-1]
            # Extract the actual txid value from the line
            txid = txid_line.split("inscription txid: ")[-1]
            print(f"SMS sent successfully with txid: {txid}")
            return txid
        else:
            print(f"Error sending SMS: {result.stderr.strip()}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.strip()}")
        return None

def log_transaction(txid, wallet_address, pubkey_hex, original_data, filepath):
    log_entry = {
        "txid": txid,
        "wallet_address": wallet_address,
        "pubkey": pubkey_hex,
        "original_data": original_data,
        "timestamp": datetime.datetime.now().isoformat()
    }
    # Update the log location to the /sms/ folder
    script_dir = os.path.dirname(os.path.realpath(__file__))
    log_filepath = os.path.join(script_dir, 'sms', 'sent_log.json')
    
    # Ensure the sms directory exists
    os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
    
    if os.path.exists(log_filepath):
        with open(log_filepath, 'r+') as log_file:
            logs = json.load(log_file)
            logs.append(log_entry)
            log_file.seek(0)
            json.dump(logs, log_file, indent=4)
    else:
        with open(log_filepath, 'w') as log_file:
            json.dump([log_entry], log_file, indent=4)
    print(f"Transaction logged in {log_filepath}")

def main():
    pubkey_hex = input("Enter the Bitcoin public key (hex): ")
    original_data = input("Enter the data to encrypt: ")
    encrypted_data = encrypt_data(pubkey_hex, original_data.encode())
    
    # Ensure the directory exists and save the encrypted data
    script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the current script's directory
    output_filepath = os.path.join(script_dir, 'text.txt')  # Save to text.txt in the current directory
    
    save_encrypted_data(encrypted_data, output_filepath)
    
    wallet_address = input("Enter the Dogecoin wallet address to send the message: ")
    txid = mint_sms(wallet_address, output_filepath)
    
    if txid:
        log_transaction(txid, wallet_address, pubkey_hex, original_data, output_filepath)

if __name__ == "__main__":
    main()
