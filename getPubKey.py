import configparser
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import hashlib
import base58
import ecdsa

DOGECOIN_PREFIX = b'\x1e'  # Dogecoin mainnet prefix for P2PKH addresses
BELLSCOIN_PREFIX = b'\x19'  # Bellscoin mainnet prefix for P2PKH addresses (you may need to verify this)

def load_rpc_config(coin_type, config_file='rpc.conf'):
    config = configparser.ConfigParser()
    config.read(config_file)

    section = f'{coin_type}_rpc'
    rpc_user = config.get(section, 'user')
    rpc_password = config.get(section, 'password')
    rpc_host = config.get(section, 'host')
    rpc_port = config.get(section, 'port')

    return rpc_user, rpc_password, rpc_host, rpc_port

def connect_to_rpc(coin_type):
    rpc_user, rpc_password, rpc_host, rpc_port = load_rpc_config(coin_type)
    rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"
    return AuthServiceProxy(rpc_url)

def get_public_keys_from_tx(txid):
    for coin_type in ['dogecoin', 'bellscoin']:
        try:
            rpc_connection = connect_to_rpc(coin_type)
            raw_tx = rpc_connection.getrawtransaction(txid, 1)
            pubkeys_with_addresses = []

            for vin in raw_tx['vin']:
                if 'txinwitness' in vin:
                    # SegWit transaction
                    pubkey = vin['txinwitness'][1]
                    if len(pubkey) in [66, 130]:  # Check for valid public key length
                        address = derive_address_from_pubkey(pubkey, coin_type)
                        pubkeys_with_addresses.append((pubkey, address))
                elif 'scriptSig' in vin and 'asm' in vin['scriptSig']:
                    # Legacy transaction
                    parts = vin['scriptSig']['asm'].split()
                    if len(parts) > 1 and len(parts[1]) in [66, 130]:  # Check for valid public key length
                        pubkey = parts[1]
                        address = derive_address_from_pubkey(pubkey, coin_type)
                        pubkeys_with_addresses.append((pubkey, address))

            return pubkeys_with_addresses, coin_type

        except JSONRPCException as e:
            if "No such mempool or blockchain transaction" in str(e):
                print(f"Transaction not found in {coin_type} blockchain, trying next...")
            else:
                print(f"Error with {coin_type} RPC: {str(e)}")
        except Exception as e:
            print(f"Unexpected error with {coin_type} RPC: {str(e)}")

    return None, None  # If transaction is not found in either blockchain

def derive_address_from_pubkey(pubkey, coin_type):
    try:
        pubkey_bytes = bytes.fromhex(pubkey)
        sha256_hash = hashlib.sha256(pubkey_bytes).digest()
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()

        # Add appropriate prefix
        if coin_type == 'dogecoin':
            prefixed_hash = DOGECOIN_PREFIX + ripemd160_hash
        elif coin_type == 'bellscoin':
            prefixed_hash = BELLSCOIN_PREFIX + ripemd160_hash
        else:
            raise ValueError("Unsupported coin type")

        # Double SHA256 for checksum
        checksum = hashlib.sha256(hashlib.sha256(prefixed_hash).digest()).digest()[:4]

        # Create final binary address
        binary_address = prefixed_hash + checksum

        # Encode in base58
        return base58.b58encode(binary_address).decode()

    except Exception as e:
        return f"Error: {str(e)}"

# Example usage
if __name__ == "__main__":
    txid = input("Enter the transaction ID: ")
    result, coin_type = get_public_keys_from_tx(txid)
    if result:
        print(f"Transaction found in {coin_type} blockchain:")
        for pubkey, address in result:
            print(f"Public Key: {pubkey}")
            print(f"Derived Address: {address}")
            print("---")
    else:
        print("Transaction not found in either Dogecoin or Bellscoin blockchain.")