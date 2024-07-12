import json
import os
from decimal import Decimal
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Configuration
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.105"
RPC_PORT = 22555
WALLETS_DIR = "./wallets"
BLOCK_HEIGHT_LIMIT = 4609723  # Define the block height limit for tracing ordinals

class DogecoinRPC:
    def __init__(self, rpc_user, rpc_password, rpc_host='localhost', rpc_port=22555):
        self.rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

    def list_unspent(self):
        try:
            return self.rpc_connection.listunspent()
        except JSONRPCException as e:
            print(f"Error listing unspent transactions: {e}")
            return []

    def get_transaction(self, txid):
        try:
            tx = self.rpc_connection.getrawtransaction(txid, True)
            if 'blockhash' in tx:
                block = self.rpc_connection.getblock(tx['blockhash'])
                tx['blockheight'] = block['height']
            else:
                tx['blockheight'] = None
            return tx
        except JSONRPCException as e:
            print(f"Error retrieving transaction {txid}: {e}")
            return None

    def trace_ordinal_genesis(self, txid, output_index=0):
        def get_previous_tx_output(txid, vout):
            try:
                prev_tx = self.rpc_connection.getrawtransaction(txid, True)
                return prev_tx['vout'][vout]
            except JSONRPCException as e:
                print(f"An error occurred: {e}")
                return None

        def get_sigscript_asm(txid, vout):
            try:
                prev_tx = self.rpc_connection.getrawtransaction(txid, True)
                return prev_tx['vin'][vout]['scriptSig']['asm']
            except IndexError:
                print("not an ord")
                return None
            except JSONRPCException as e:
                print(f"An error occurred while fetching sigscript asm: {e}")
                return None

        def process_transaction(txid, output_index):
            try:
                transaction = self.rpc_connection.getrawtransaction(txid, True)
            except JSONRPCException as e:
                print(f"An error occurred: {e}")
                return None, None

            vins = transaction['vin']
            vouts = transaction['vout']

            vin_values = []
            vin_details = []
            for vin in vins:
                prev_tx_output = get_previous_tx_output(vin['txid'], vin['vout'])
                if prev_tx_output:
                    vin_values.append(prev_tx_output['value'])
                    vin_details.append((vin['txid'], vin['vout']))
                else:
                    vin_values.append(Decimal('0'))
                    vin_details.append((vin['txid'], vin['vout']))

            vin_remaining_values = vin_values[:]

            chosen_vout_info = None
            for vout_index, vout in enumerate(vouts):
                remaining_value = vout['value']
                corresponding_vins = []
                
                for vin_index, vin_value in enumerate(vin_remaining_values):
                    if remaining_value > 0 and vin_remaining_values[vin_index] > 0:
                        if vin_remaining_values[vin_index] >= remaining_value:
                            vin_remaining_values[vin_index] -= remaining_value
                            corresponding_vins.append(vin_index)
                            remaining_value = 0
                        else:
                            remaining_value -= vin_remaining_values[vin_index]
                            corresponding_vins.append(vin_index)
                            vin_remaining_values[vin_index] = 0

                if vout_index == output_index:
                    chosen_vout_info = {
                        "vout_index": vout_index,
                        "value": vout['value'],
                        "corresponding_vins": corresponding_vins
                    }

            if chosen_vout_info and chosen_vout_info['corresponding_vins']:
                for vin_index in chosen_vout_info['corresponding_vins']:
                    vin_txid, vout_idx = vin_details[vin_index]
                    sigscript_asm = get_sigscript_asm(vin_txid, vout_idx)
                    if sigscript_asm is None:
                        return None, None
                    if sigscript_asm.split()[0] == "6582895":
                        ord_genesis = vin_txid
                        print(f"Stopping loop as sigscript asm index 0 equals 6582895")
                        print(f"ord_genesis: {ord_genesis}")
                        return ord_genesis
                    print(f"Previous TXID: {vin_txid}, VOUT Index: {vout_idx}, SigScript ASM: {sigscript_asm}")
                    return vin_txid, vout_idx
            else:
                return None, None

        current_txid = txid
        current_output_index = output_index

        while current_txid is not None:
            result = process_transaction(current_txid, current_output_index)
            if isinstance(result, str):  # If result is a genesis txid
                return result
            current_txid, current_output_index = result

        return None

def list_wallet_addresses(dogecoin_rpc):
    utxos = dogecoin_rpc.list_unspent()
    addresses = {utxo['address'] for utxo in utxos}
    return list(addresses)

def read_existing_utxos(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def create_utxo_files(dogecoin_rpc):
    utxos = dogecoin_rpc.list_unspent()
    utxos_by_address = {}

    # Group UTXOs by address
    for utxo in utxos:
        address = utxo['address']
        if address not in utxos_by_address:
            utxos_by_address[address] = []
        amount = Decimal(utxo['amount'])
        genesis_txid = "not an ord"
        
        if amount == Decimal('0.001'):
            filename = os.path.join(WALLETS_DIR, f"{address}.json")
            existing_utxos = read_existing_utxos(filename)
            existing_txids = {(existing_utxo['txid'], existing_utxo['vout']) for existing_utxo in existing_utxos}
            
            if (utxo['txid'], utxo['vout']) not in existing_txids:
                print(f"Tracing ordinals for UTXO: {utxo['txid']} with amount {utxo['amount']}")
                genesis_txid = dogecoin_rpc.trace_ordinal_genesis(utxo['txid'], utxo['vout'])

        utxos_by_address[address].append({
            'txid': utxo['txid'],
            'vout': utxo['vout'],
            'amount': float(amount),  # Convert Decimal to float
            'genesis_txid': genesis_txid
        })

    # Ensure the wallets directory exists
    if not os.path.exists(WALLETS_DIR):
        os.makedirs(WALLETS_DIR)

    # Create or update a JSON file for each address in the wallets directory
    for address, new_utxos in utxos_by_address.items():
        filename = os.path.join(WALLETS_DIR, f"{address}.json")
        existing_utxos = read_existing_utxos(filename)

        # Merge new UTXOs with existing UTXOs
        existing_utxos_dict = {(existing_utxo['txid'], existing_utxo['vout']): existing_utxo for existing_utxo in existing_utxos}
        for utxo in new_utxos:
            if (utxo['txid'], utxo['vout']) in existing_utxos_dict:
                # Preserve the existing genesis_txid
                utxo['genesis_txid'] = existing_utxos_dict[(utxo['txid'], utxo['vout'])]['genesis_txid']
            existing_utxos_dict[(utxo['txid'], utxo['vout'])] = utxo
        merged_utxos = list(existing_utxos_dict.values())

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
        amount = Decimal(utxo['amount'])
        genesis_txid = "not an ord"

        filename = os.path.join(WALLETS_DIR, f"{address}.json")
        existing_utxos = read_existing_utxos(filename)
        existing_txids = {(existing_utxo['txid'], existing_utxo['vout']) for existing_utxo in existing_utxos}

        if (utxo['txid'], utxo['vout']) not in existing_txids:
            if amount == Decimal('0.001'):
                print(f"Tracing ordinals for UTXO: {utxo['txid']} with amount {utxo['amount']}")
                genesis_txid = dogecoin_rpc.trace_ordinal_genesis(utxo['txid'], utxo['vout'])
        else:
            # If UTXO already exists, use the existing genesis_txid
            existing_utxo = next(
                (existing_utxo for existing_utxo in existing_utxos if existing_utxo['txid'] == utxo['txid'] and existing_utxo['vout'] == utxo['vout']),
                None
            )
            if existing_utxo:
                genesis_txid = existing_utxo['genesis_txid']

        utxos_by_address[address].append({
            'txid': utxo['txid'],
            'vout': utxo['vout'],
            'amount': float(amount),  # Convert Decimal to float
            'genesis_txid': genesis_txid
        })

    # Iterate over each JSON file in the wallets directory
    for filename in os.listdir(WALLETS_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(WALLETS_DIR, filename)
            existing_utxos = read_existing_utxos(file_path)

            # Extract the address from the filename
            address = os.path.splitext(filename)[0]

            # Verify each UTXO in the JSON file
            updated_utxos = [
                utxo for utxo in existing_utxos
                if (utxo['txid'], utxo['vout']) in {(utxo['txid'], utxo['vout']) for utxo in utxos_by_address.get(address, [])}
            ]

            # Add new UTXOs if they are not already in the file
            existing_utxos_dict = {(existing_utxo['txid'], existing_utxo['vout']): existing_utxo for existing_utxo in updated_utxos}
            for utxo in utxos_by_address.get(address, []):
                if (utxo['txid'], utxo['vout']) not in existing_utxos_dict:
                    existing_utxos_dict[(utxo['txid'], utxo['vout'])] = utxo

            # Save the updated UTXO list back to the JSON file
            with open(file_path, 'w') as f:
                json.dump(list(existing_utxos_dict.values()), f, indent=4)

            print(f"Updated file {file_path}: {len(existing_utxos)} -> {len(list(existing_utxos_dict.values()))} UTXOs")

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
