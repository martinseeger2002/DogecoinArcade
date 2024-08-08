import configparser
from bitcoinrpc.authproxy import AuthServiceProxy
import hashlib
import base58
import ecdsa

DOGECOIN_PREFIX = b'\x1e'  # Dogecoin mainnet prefix for P2PKH addresses

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

def get_public_keys_from_tx(txid):
    rpc_connection = connect_to_rpc()
    raw_tx = rpc_connection.getrawtransaction(txid, 1)
    pubkeys_with_addresses = []

    for vin in raw_tx['vin']:
        if 'txinwitness' in vin:
            # SegWit transaction
            pubkey = vin['txinwitness'][1]
            if len(pubkey) in [66, 130]:  # Check for valid public key length
                address = derive_dogecoin_address_from_pubkey(pubkey)
                pubkeys_with_addresses.append((pubkey, address))
        elif 'scriptSig' in vin and 'asm' in vin['scriptSig']:
            # Legacy transaction
            parts = vin['scriptSig']['asm'].split()
            if len(parts) > 1 and len(parts[1]) in [66, 130]:  # Check for valid public key length
                pubkey = parts[1]
                address = derive_dogecoin_address_from_pubkey(pubkey)
                pubkeys_with_addresses.append((pubkey, address))

    return pubkeys_with_addresses

def derive_dogecoin_address_from_pubkey(pubkey):
    try:
        pubkey_bytes = bytes.fromhex(pubkey)
        sha256_hash = hashlib.sha256(pubkey_bytes).digest()
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()

        # Add Dogecoin prefix
        prefixed_hash = DOGECOIN_PREFIX + ripemd160_hash

        # Double SHA256 for checksum
        checksum = hashlib.sha256(hashlib.sha256(prefixed_hash).digest()).digest()[:4]

        # Create final binary address
        binary_address = prefixed_hash + checksum

        # Encode in base58
        return base58.b58encode(binary_address).decode()

    except Exception as e:
        return f"Error: {str(e)}"
