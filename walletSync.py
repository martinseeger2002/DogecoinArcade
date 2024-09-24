import configparser
import json
import os
import time
from decimal import Decimal
from datetime import datetime
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from urllib.parse import quote

# Load RPC credentials from rpc.conf
config = configparser.ConfigParser()
config.read('rpc.conf')

WALLETS_DIR = "./wallets"
BLOCK_HEIGHT_LIMIT = 4609723  # Define the block height limit for tracing ordinals

class CoinRPC:
    def __init__(self, coin_type):
        self.coin_type = coin_type
        self.rpc_user = config.get(coin_type, 'user')
        self.rpc_password = config.get(coin_type, 'password')
        self.rpc_host = config.get(coin_type, 'host')
        self.rpc_port = config.getint(coin_type, 'port')
        self.rpc_connection = None
        self.connect()

    def connect(self):
        rpc_url = f"http://{self.rpc_user}:{self.rpc_password}@{self.rpc_host}:{self.rpc_port}"
        self.rpc_connection = AuthServiceProxy(rpc_url)

    def get_wallet_rpc(self, wallet_name):
        encoded_wallet = quote(wallet_name)
        wallet_url = f"http://{self.rpc_user}:{self.rpc_password}@{self.rpc_host}:{self.rpc_port}/wallet/{encoded_wallet}"
        return AuthServiceProxy(wallet_url)

    def list_wallets(self):
        try:
            return self.rpc_connection.listwallets()
        except JSONRPCException as e:
            print(f"Error listing wallets for {self.coin_type}: {e}")
            return []

    def list_addresses(self):
        if self.coin_type == 'bellscoin_rpc':
            return self.list_bellscoin_addresses()
        else:
            try:
                received = self.rpc_connection.listreceivedbyaddress(0, True)
                return [entry['address'] for entry in received]
            except JSONRPCException as e:
                print(f"Error listing addresses for {self.coin_type}: {e}")
                return []

    def list_bellscoin_addresses(self):
        all_addresses = set()
        for wallet in self.list_wallets():
            wallet_rpc = self.get_wallet_rpc(wallet)
            try:
                unspent = wallet_rpc.listunspent(0)
                addresses = set(utxo['address'] for utxo in unspent if 'address' in utxo)
                all_addresses.update(addresses)
            except JSONRPCException as e:
                print(f"Error listing addresses for wallet {wallet}: {e}")
        return list(all_addresses)

    def list_unspent(self, address=None):
        if self.coin_type == 'bellscoin_rpc':
            return self.list_bellscoin_unspent(address)
        else:
            try:
                if address:
                    return [utxo for utxo in self.rpc_connection.listunspent(0) if utxo.get('address') == address]
                else:
                    return self.rpc_connection.listunspent(0)
            except JSONRPCException as e:
                print(f"Error listing unspent transactions for {self.coin_type}: {e}")
                return []

    def list_bellscoin_unspent(self, address=None):
        all_unspent = []
        for wallet in self.list_wallets():
            wallet_rpc = self.get_wallet_rpc(wallet)
            try:
                if address:
                    unspent = [utxo for utxo in wallet_rpc.listunspent(0) if utxo.get('address') == address]
                else:
                    unspent = wallet_rpc.listunspent(0)
                all_unspent.extend(unspent)
            except JSONRPCException as e:
                print(f"Error listing unspent for wallet {wallet}: {e}")
        return all_unspent

    def get_transaction(self, txid):
        try:
            tx = self.rpc_connection.getrawtransaction(txid, True)
            if 'blockhash' in tx:
                block = self.rpc_connection.getblock(tx['blockhash'])
                tx['blocktime'] = block['time']
            else:
                tx['blocktime'] = None
            return tx
        except JSONRPCException as e:
            print(f"Error retrieving transaction {txid}: {e}")
            return None

    def get_previous_tx_output(self, txid, vout):
        try:
            prev_tx = self.get_transaction(txid)
            return prev_tx['vout'][vout] if prev_tx else None
        except JSONRPCException as e:
            print(f"An error occurred: {e}")
            return None

    def get_sender_address(self, txid):
        try:
            prev_tx = self.get_transaction(txid)
            if prev_tx and len(prev_tx['vout']) > 1:
                output = prev_tx['vout'][1]
                if 'scriptPubKey' in output and 'addresses' in output['scriptPubKey']:
                    return output['scriptPubKey']['addresses'][0]
            return None
        except JSONRPCException as e:
            print(f"An error occurred: {e}")
            return None

    def get_sigscript_asm(self, txid, vout):
        try:
            prev_tx = self.get_transaction(txid)
            return prev_tx['vin'][vout]['scriptSig']['asm'] if prev_tx else None
        except IndexError:
            print("Not an ord")
            return None
        except JSONRPCException as e:
            print(f"An error occurred while fetching sigscript asm: {e}")
            return None

    def reverse_and_flip_pairs(self, hex_string):
        # First, reverse the entire string
        reversed_string = hex_string[::-1]
        # Then, flip each pair of characters
        flipped_pairs_string = ''.join([reversed_string[i+1] + reversed_string[i] for i in range(0, len(reversed_string), 2)])
        return flipped_pairs_string

    def trace_ordinal_and_sms(self, txid, output_index=0):
        def process_transaction(txid, output_index):
            transaction = self.get_transaction(txid)
            if not transaction:
                return None, None

            vins = transaction['vin']
            vouts = transaction['vout']

            vin_values = []
            vin_details = []
            for vin in vins:
                prev_tx_output = self.get_previous_tx_output(vin['txid'], vin['vout'])
                if prev_tx_output:
                    vin_values.append(prev_tx_output['value'])
                    sender_address = self.get_sender_address(vin['txid'])
                    vin_details.append((vin['txid'], vin['vout'], sender_address))
                else:
                    vin_values.append(Decimal('0'))
                    vin_details.append((vin['txid'], vin['vout'], 'Unknown'))

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
                    vin_txid, vout_idx, sender_address = vin_details[vin_index]
                    sigscript_asm = self.get_sigscript_asm(vin_txid, vout_idx)
                    if sigscript_asm is None:
                        return None, None
                    
                    asm_parts = sigscript_asm.split()

                    if asm_parts[0] == "6582895":
                        if asm_parts[2] == "0" and asm_parts[5] == "11":
                            # Handle delegate child
                            delegate_child_txid = vin_txid
                            genesis_txid_flipped = self.reverse_and_flip_pairs(asm_parts[6])
                            print(f"Delegate child transaction detected: {delegate_child_txid}")
                            print(f"Reversed and flipped genesis txid: {genesis_txid_flipped}")
                            return {
                                "genesis_txid": genesis_txid_flipped,
                                "child_txid": delegate_child_txid,
                                "sender_address": sender_address
                            }
                        else:
                            ord_genesis = vin_txid
                            print(f"Ord genesis transaction detected: {ord_genesis}")
                            return {"genesis_txid": ord_genesis, "sender_address": sender_address}
                    elif asm_parts[0] == "7564659":
                        sms_txid = vin_txid
                        print(f"SMS transaction detected: {sms_txid}")
                        return {"sms_txid": sms_txid, "sender_address": sender_address}
                    
                    print(f"Previous TXID: {vin_txid}, VOUT Index: {vout_idx}, SigScript ASM: {sigscript_asm}")
                    return vin_txid, vout_idx
            else:
                return None, None

        # Check the initial transaction for the genesis sigscript asm or sms sigscript asm
        initial_sigscript_asm = self.get_sigscript_asm(txid, output_index)
        if initial_sigscript_asm:
            sender_address = self.get_sender_address(txid)
            asm_parts = initial_sigscript_asm.split()
            
            if asm_parts[0] == "6582895":
                if asm_parts[2] == "0" and asm_parts[5] == "11":
                    # Handle delegate child
                    delegate_child_txid = txid
                    genesis_txid_flipped = self.reverse_and_flip_pairs(asm_parts[6])
                    print(f"Delegate child transaction detected in initial tx: {delegate_child_txid}")
                    print(f"Reversed and flipped genesis txid: {genesis_txid_flipped}")
                    return {
                        "genesis_txid": genesis_txid_flipped,
                        "child_txid": delegate_child_txid,
                        "sender_address": sender_address
                    }
                else:
                    print(f"Initial transaction {txid} is the genesis transaction.")
                    return {"genesis_txid": txid, "sender_address": sender_address}
            elif asm_parts[0] == "7564659":
                print(f"Initial transaction {txid} is the sms transaction.")
                return {"sms_txid": txid, "sender_address": sender_address}

        current_txid = txid
        current_output_index = output_index

        while current_txid is not None:
            result = process_transaction(current_txid, current_output_index)
            if isinstance(result, dict):  # If result is a dict containing genesis_txid or sms_txid
                return result
            current_txid, current_output_index = result

        return None

    def get_mime_type(self, genesis_txid):
        try:
            print(f"Attempting to get MIME type for genesis txid: {genesis_txid}")
            tx = self.rpc_connection.getrawtransaction(genesis_txid, True)
            if tx and 'vin' in tx and len(tx['vin']) > 0:
                script_sig = tx['vin'][0].get('scriptSig', {})
                if 'asm' in script_sig:
                    asm_parts = script_sig['asm'].split()
                    print(f"ScriptSig ASM parts: {asm_parts}")
                    if len(asm_parts) > 2:
                        mime_type_hex = asm_parts[2]  # Get the third element (index 2)
                        try:
                            mime_type = bytes.fromhex(mime_type_hex).decode('utf-8')
                            print(f"Found MIME type: {mime_type}")
                            return mime_type
                        except Exception as e:
                            print(f"Error decoding MIME type: {e}")
                    else:
                        print("ScriptSig ASM has insufficient parts")
                else:
                    print("No 'asm' in scriptSig")
            else:
                print("Transaction does not have expected structure")
        except Exception as e:
            print(f"Error getting MIME type for genesis txid {genesis_txid}: {e}")
        return None

def read_existing_utxos(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def process_wallet_utxos(coin_rpc, address):
    filename = os.path.join(WALLETS_DIR, f"{address}.json")
    existing_utxos = read_existing_utxos(filename)
    existing_utxos_dict = {(utxo['txid'], utxo['vout']): utxo for utxo in existing_utxos}

    current_utxos = coin_rpc.list_unspent(address)
    current_utxos_set = {(utxo['txid'], utxo['vout']) for utxo in current_utxos}

    updated_utxos = []
    for utxo in current_utxos:
        if utxo['address'] == address:
            utxo_key = (utxo['txid'], utxo['vout'])
            if utxo_key in existing_utxos_dict:
                # Use existing data if available
                updated_utxo = existing_utxos_dict[utxo_key]
            else:
                # Process new UTXO
                updated_utxo = process_new_utxo(coin_rpc, utxo)
            updated_utxos.append(updated_utxo)

    # Remove UTXOs that are no longer in the wallet
    updated_utxos = [utxo for utxo in updated_utxos if (utxo['txid'], utxo['vout']) in current_utxos_set]

    if not updated_utxos:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Removed file {filename} as the wallet has no UTXOs")
    else:
        # Write updated UTXOs back to file
        with open(filename, 'w') as f:
            json.dump(updated_utxos, f, indent=4)
        print(f"Updated file {filename} with {len(updated_utxos)} UTXOs")

def process_new_utxo(coin_rpc, utxo):
    amount = Decimal(utxo['amount'])
    genesis_txid = "not an ord"
    sms_txid = "not an sms"
    timestamp = None
    sender_address = None
    child_txid = None
    mime_type = None

    print(f"Processing new UTXO: {utxo['txid']} with amount {utxo['amount']}")
    trace_result = coin_rpc.trace_ordinal_and_sms(utxo['txid'], utxo['vout'])
    if trace_result:
        sms_txid = trace_result.get("sms_txid", sms_txid)
        sender_address = trace_result.get("sender_address", sender_address)
        child_txid = trace_result.get("child_txid", child_txid)
        if sms_txid != "not an sms":
            genesis_txid = "encrypted message"
        else:
            genesis_txid = trace_result.get("genesis_txid", genesis_txid)
        
        # Always attempt to get MIME type for genesis transactions
        if genesis_txid != "not an ord" and genesis_txid != "encrypted message":
            mime_type = coin_rpc.get_mime_type(genesis_txid)
            print(f"MIME type for {genesis_txid}: {mime_type}")

    tx_details = coin_rpc.get_transaction(utxo['txid'])
    if tx_details and 'blocktime' in tx_details:
        timestamp = datetime.utcfromtimestamp(tx_details['blocktime']).strftime('%Y-%m-%d %H:%M:%S')

    return {
        'txid': utxo['txid'],
        'vout': utxo['vout'],
        'amount': float(amount),
        'genesis_txid': genesis_txid,
        'sms_txid': sms_txid,
        'child_txid': child_txid,
        'timestamp': timestamp,
        'sender_address': sender_address,
        'coin_type': coin_rpc.coin_type,
        'mime_type': mime_type
    }

def process_all_addresses(coin_rpc):
    addresses = coin_rpc.list_addresses()
    for address in addresses:
        print(f"Processing address: {address}")
        try:
            process_wallet_utxos(coin_rpc, address)
        except Exception as e:
            print(f"An error occurred while processing address {address}: {e}")

if __name__ == "__main__":
    default_section = config['default']
    for coin in ['primary', 'fallback', 'secondary', 'tertiary']:
        if coin in default_section:
            coin_type = default_section[coin]
            print(f"\nProcessing {coin_type.capitalize()} addresses:")
            try:
                coin_rpc = CoinRPC(coin_type)
                if coin_rpc.rpc_connection:
                    process_all_addresses(coin_rpc)
                else:
                    print(f"Skipping {coin_type} due to connection failure")
            except Exception as e:
                print(f"An error occurred while processing {coin_type} addresses: {e}")