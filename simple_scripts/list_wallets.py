import json
import os
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Configuration
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.105"
RPC_PORT = 22555
WALLETS_DIR = "./wallets"

class DogecoinRPC:
    def __init__(self, rpc_user, rpc_password, rpc_host='localhost', rpc_port=22555):
        self.rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

    def list_unspent(self):
        try:
            return self.rpc_connection.listunspent()
        except JSONRPCException as e:
            print(f"Error listing unspent transactions: {e}")
            return []

def list_wallet_addresses(dogecoin_rpc):
    utxos = dogecoin_rpc.list_unspent()
    addresses = {utxo['address'] for utxo in utxos}
    return list(addresses)

def create_utxo_files(dogecoin_rpc):
    utxos = dogecoin_rpc.list_unspent()
    utxos_by_address = {}

    # Group UTXOs by address
    for utxo in utxos:
        address = utxo['address']
        if address not in utxos_by_address:
            utxos_by_address[address] = []
        utxos_by_address[address].append({
            'txid': utxo['txid'],
            'vout': utxo['vout'],
            'amount': float(utxo['amount'])  # Convert Decimal to float
        })

    # Ensure the wallets directory exists
    if not os.path.exists(WALLETS_DIR):
        os.makedirs(WALLETS_DIR)

    # Create or update a JSON file for each address in the wallets directory
    for address, new_utxos in utxos_by_address.items():
        filename = os.path.join(WALLETS_DIR, f"{address}.json")
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                existing_utxos = json.load(f)
            # Merge new UTXOs with existing UTXOs
            existing_utxos_dict = {(utxo['txid'], utxo['vout']): utxo for utxo in existing_utxos}
            for utxo in new_utxos:
                existing_utxos_dict[(utxo['txid'], utxo['vout'])] = utxo
            merged_utxos = list(existing_utxos_dict.values())
        else:
            merged_utxos = new_utxos

        # Write the merged UTXOs back to the file
        with open(filename, 'w') as f:
            json.dump(merged_utxos, f, indent=4)
        print(f"Created or updated file {filename} with UTXOs for address {address}")

def verify_and_update_utxo_files(dogecoin_rpc):
    utxos = dogecoin_rpc.list_unspent()
    utxos_by_address = {}

    # Group UTXOs by address
    for utxo in utxos:
        address = utxo['address']
        if address not in utxos_by_address:
            utxos_by_address[address] = []
        utxos_by_address[address].append({
            'txid': utxo['txid'],
            'vout': utxo['vout'],
            'amount': float(utxo['amount'])  # Convert Decimal to float
        })

    # Iterate over each JSON file in the wallets directory
    for filename in os.listdir(WALLETS_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(WALLETS_DIR, filename)
            if os.path.exists(file_path):  # Check if the file exists
                with open(file_path, 'r') as f:
                    utxos_in_file = json.load(f)

                # Extract the address from the filename
                address = os.path.splitext(filename)[0]

                # Verify each UTXO in the JSON file
                updated_utxos = [
                    utxo for utxo in utxos_in_file
                    if (utxo['txid'], utxo['vout']) in {(utxo['txid'], utxo['vout']) for utxo in utxos_by_address.get(address, [])}
                ]

                # Add new UTXOs if they are not already in the file
                existing_utxos_dict = {(utxo['txid'], utxo['vout']): utxo for utxo in updated_utxos}
                for utxo in utxos_by_address.get(address, []):
                    if (utxo['txid'], utxo['vout']) not in existing_utxos_dict:
                        updated_utxos.append(utxo)

                # Save the updated UTXO list back to the JSON file
                with open(file_path, 'w') as f:
                    json.dump(updated_utxos, f, indent=4)

                print(f"Updated file {file_path}: {len(utxos_in_file)} -> {len(updated_utxos)} UTXOs")

if __name__ == "__main__":
    dogecoin_rpc = DogecoinRPC(RPC_USER, RPC_PASSWORD, RPC_HOST, RPC_PORT)

    print("Listing public addresses from the default wallet:")
    addresses = list_wallet_addresses(dogecoin_rpc)
    for address in addresses:
        print(f"Address: {address}")

    print("\nCreating UTXO files for each address:")
    create_utxo_files(dogecoin_rpc)

    print("\nVerifying and updating UTXO files:")
    verify_and_update_utxo_files(dogecoin_rpc)
