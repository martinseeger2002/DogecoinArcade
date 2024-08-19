import base58
import base64
import json
import os
import mimetypes
from datetime import datetime
import configparser
from bitcoinrpc.authproxy import AuthServiceProxy
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import getPubKey  # Assuming getPubKey is available and works as described
import getPrivKey  # Assuming getPrivKey is available and works as described

def find_wallet_for_txid(txid, wallets_dir="./wallets"):
    """Find the wallet containing the UTXO with the given txid."""
    for wallet_filename in os.listdir(wallets_dir):
        if wallet_filename.endswith(".json"):
            wallet_address = os.path.splitext(wallet_filename)[0]
            wallet_file_path = os.path.join(wallets_dir, wallet_filename)
            with open(wallet_file_path, "r") as wallet_file:
                wallet_data = json.load(wallet_file)
                for utxo in wallet_data:
                    if utxo["sms_txid"] == txid:
                        return wallet_address
    return None

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

def get_nickname_from_address_book(pubkey, address, address_book_path="./sms/addressBook.json"):
    with open(address_book_path, "r") as address_book_file:
        address_book = json.load(address_book_file)
        for entry in address_book:
            if entry['pubkey'] == pubkey and entry['address'] == address:
                return entry['nickname']
    return "Unknown"

def append_to_json_file(file_path, new_data):
    if os.path.exists(file_path):
        with open(file_path, "r+") as file:
            existing_data = json.load(file)
            existing_data.append(new_data)  # Add the new data to the list

            # Sort the list by the 'timestamp' field in descending order
            existing_data.sort(key=lambda x: x['timestamp'], reverse=True)

            file.seek(0)
            json.dump(existing_data, file, indent=4)
            file.truncate()  # Ensure any leftover data is removed
    else:
        with open(file_path, "w") as file:
            json.dump([new_data], file, indent=4)

def save_decrypted_file(txid, mimetype, decrypted_data):
    output_dir = "./smscontent"
    os.makedirs(output_dir, exist_ok=True)

    # Manually handle common MIME types
    mime_extension_map = {
        'image/webp': '.webp',
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'text/plain': '.txt',
        # Add more mappings as necessary
    }

    # Try to guess the extension; fallback to manual mapping
    extension = mimetypes.guess_extension(mimetype) or mime_extension_map.get(mimetype)

    if extension is None:
        print(f"Unhandled MIME type: {mimetype}, could not determine a valid extension.")
        return None

    output_file_path = os.path.join(output_dir, f"{txid}{extension}")

    # Handle different types of files appropriately
    if "text" in mimetype:
        with open(output_file_path, "w") as file:
            file.write(decrypted_data.decode())
    else:
        with open(output_file_path, "wb") as file:
            file.write(decrypted_data)

    print(f"Decrypted file saved to {output_file_path}")
    return output_file_path

def decrypt_file(txid, sms_data, privkey, wallet_address, rpc_connection):
    encrypted_data_base64 = sms_data['encrypted_data']
    mimetype = sms_data['mimetype']

    # Decode the encrypted data
    encrypted_data = base64.b64decode(encrypted_data_base64)
    encrypted_aes_key = encrypted_data[:33+12+32+16]
    encrypted_message = encrypted_data[33+12+32+16:]

    # Decrypt the AES key and the data
    aes_key = decrypt_aes_key_with_privkey(privkey, encrypted_aes_key)
    decrypted_data = decrypt_data_with_aes(aes_key, encrypted_message)

    # Decode data if necessary
    if mimetype != "text/plain":
        decrypted_data = base64.b64decode(decrypted_data)

    # Save the decrypted file
    output_file_path = save_decrypted_file(txid, mimetype, decrypted_data)

    # Only proceed if the file was saved successfully
    if output_file_path is not None:
        # Fetch public key and address associated with the transaction
        pubkeys_with_addresses = getPubKey.get_public_keys_from_tx(txid)
        pubkey, address = pubkeys_with_addresses[0]  # Assuming first entry is what we need

        # Get nickname from address book
        nickname = get_nickname_from_address_book(pubkey, address)

        # Fetch the transaction details to get the blockhash
        tx_details = rpc_connection.getrawtransaction(txid, 1)
        blockhash = tx_details["blockhash"]

        # Fetch the block details to get the block time
        block_details = rpc_connection.getblock(blockhash)
        timestamp = datetime.utcfromtimestamp(block_details["time"]).isoformat()

        # Handle data field in sms_data JSON
        if mimetype != "text/plain" and "data" in sms_data:
            data_content = sms_data["data"]
        else:
            data_content = decrypted_data.decode() if mimetype == "text/plain" else ""

        # Prepare the new JSON content
        new_json_data = {
            "nickname": nickname,
            "pubkey": pubkey,
            "address": address,
            "mimetype": mimetype,
            "data": data_content,
            "sms_txid": txid,
            "receiving_address": wallet_address,  # Add the receiving address used to get the privKey         
            "timestamp": timestamp,  # Use blockchain timestamp
            "tag": "received",
            "read": "false"
        }

        # Determine the JSON file path and append the data using the address as the filename
        output_json_dir = "./smslogs"
        os.makedirs(output_json_dir, exist_ok=True)
        output_json_file_path = os.path.join(output_json_dir, f"{address}.json")

        append_to_json_file(output_json_file_path, new_json_data)

        print(f"Decrypted data appended to {output_json_file_path}")

        # Delete the original .json file after processing
        json_file_path = os.path.join("./smscontent", f"{txid}.json")
        if os.path.exists(json_file_path):
            os.remove(json_file_path)
            print(f"Deleted original file: {json_file_path}")
    else:
        print(f"File for transaction {txid} was not saved. Original content not deleted.")

def load_rpc_config(config_file='rpc.conf'):
    config = configparser.ConfigParser()
    config.read(config_file)

    rpc_user = config.get('rpc', 'user')
    rpc_password = config.get('rpc', 'password')
    rpc_host = config.get('rpc', 'host')
    rpc_port = config.get('rpc', 'port')

    return rpc_user, rpc_password, rpc_host, rpc_port

def connect_to_rpc():
    rpc_user, rpc_password, rpc_host, rpc_port = load_rpc_config()
    rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"
    return AuthServiceProxy(rpc_url)

def main():
    # Connect to RPC
    rpc_connection = connect_to_rpc()

    # Iterate over each .json file in the /smscontent directory
    smscontent_dir = "./smscontent"
    for filename in os.listdir(smscontent_dir):
        if filename.endswith(".json"):
            txid = os.path.splitext(filename)[0]
            input_file_path = os.path.join(smscontent_dir, filename)

            # Load the JSON content
            with open(input_file_path, "r") as json_file:
                sms_data = json.load(json_file)

            # Find the wallet containing the UTXO for this txid
            wallet_address = find_wallet_for_txid(txid)
            if wallet_address is None:
                print(f"Wallet containing txid {txid} not found.")
                continue

            # Retrieve the private key for the wallet address
            privkey = getPrivKey.get_private_key(wallet_address)
            ec_privkey = privkey_to_ec_privkey(privkey)

            # Decrypt the file and save the output
            decrypt_file(txid, sms_data, ec_privkey, wallet_address, rpc_connection)

if __name__ == "__main__":
    main()
