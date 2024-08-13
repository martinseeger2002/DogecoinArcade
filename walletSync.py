import configparser
import json
import os
import time
from decimal import Decimal
from datetime import datetime
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Load RPC credentials from rpc.conf
config = configparser.ConfigParser()
config.read('rpc.conf')

RPC_USER = config.get('rpc', 'user')
RPC_PASSWORD = config.get('rpc', 'password')
RPC_HOST = config.get('rpc', 'host')
RPC_PORT = config.getint('rpc', 'port')

WALLETS_DIR = "./wallets"
BLOCK_HEIGHT_LIMIT = 4609723  # Define the block height limit for tracing ordinals

class DogecoinRPC:
    def __init__(self, rpc_user, rpc_password, rpc_host='localhost', rpc_port=22555):
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.rpc_host = rpc_host
        self.rpc_port = rpc_port
        self.rpc_connection = None
        self.connect()

    def connect(self):
        self.rpc_connection = AuthServiceProxy(f"http://{self.rpc_user}:{self.rpc_password}@{self.rpc_host}:{self.rpc_port}")

    def disconnect(self):
        self.rpc_connection = None

    def reconnect(self):
        self.disconnect()
        self.connect()

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
                tx['blocktime'] = block['time']  # Add block time (timestamp)
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
                    if sigscript_asm.split()[0] == "6582895":
                        ord_genesis = vin_txid
                        print(f"Stopping loop as sigscript asm index 0 equals 6582895")
                        print(f"ord_genesis: {ord_genesis}")
                        return {"genesis_txid": ord_genesis, "sender_address": sender_address}
                    elif sigscript_asm.split()[0] == "7564659":
                        sms_txid = vin_txid
                        print(f"Stopping loop as sigscript asm index 0 equals 7564659")
                        print(f"sms_txid: {sms_txid}")
                        return {"sms_txid": sms_txid, "sender_address": sender_address}
                    print(f"Previous TXID: {vin_txid}, VOUT Index: {vout_idx}, SigScript ASM: {sigscript_asm}")
                    return vin_txid, vout_idx
            else:
                return None, None

        # Check the initial transaction for the genesis sigscript asm or sms sigscript asm
        initial_sigscript_asm = self.get_sigscript_asm(txid, output_index)
        if initial_sigscript_asm:
            sender_address = self.get_sender_address(txid)
            if initial_sigscript_asm.split()[0] == "6582895":
                print(f"Initial transaction {txid} is the genesis transaction.")
                return {"genesis_txid": txid, "sender_address": sender_address}
            elif initial_sigscript_asm.split()[0] == "7564659":
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

def list_wallet_addresses(dogecoin_rpc):
    utxos = dogecoin_rpc.list_unspent()
    addresses = {utxo['address'] for utxo in utxos}
    return list(addresses)

def read_existing_utxos(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def process_wallet_utxos(dogecoin_rpc, address):
    filename = os.path.join(WALLETS_DIR, f"{address}.json")
    existing_utxos = read_existing_utxos(filename)
    existing_txids = {(existing_utxo['txid'], existing_utxo['vout']) for existing_utxo in existing_utxos}

    utxos = dogecoin_rpc.list_unspent()

    new_utxos = []
    for utxo in utxos:
        if utxo['address'] == address:
            amount = Decimal(utxo['amount'])
            genesis_txid = "not an ord"
            sms_txid = "not an sms"
            timestamp = None
            sender_address = None

            if (utxo['txid'], utxo['vout']) not in existing_txids:
                if amount == Decimal('0.001'):
                    print(f"Tracing ordinals for UTXO: {utxo['txid']} with amount {utxo['amount']}")
                    trace_result = dogecoin_rpc.trace_ordinal_and_sms(utxo['txid'], utxo['vout'])
                    if trace_result:
                        sms_txid = trace_result.get("sms_txid", sms_txid)
                        sender_address = trace_result.get("sender_address", sender_address)
                        if sms_txid != "not an sms":
                            genesis_txid = "encrypted message"
                        else:
                            genesis_txid = trace_result.get("genesis_txid", genesis_txid)

                # Get the timestamp from the block and convert it to a readable format
                tx_details = dogecoin_rpc.get_transaction(utxo['txid'])
                if tx_details and 'blocktime' in tx_details:
                    timestamp = datetime.utcfromtimestamp(tx_details['blocktime']).strftime('%Y-%m-%d %H:%M:%S')

            new_utxos.append({
                'txid': utxo['txid'],
                'vout': utxo['vout'],
                'amount': float(amount),  # Convert Decimal to float
                'genesis_txid': genesis_txid,
                'sms_txid': sms_txid,
                'timestamp': timestamp,
                'sender_address': sender_address
            })

            # Reconnect after processing each UTXO
            dogecoin_rpc.reconnect()

    # Merge new UTXOs with existing UTXOs
    existing_utxos_dict = {(existing_utxo['txid'], existing_utxo['vout']): existing_utxo for existing_utxo in existing_utxos}
    for utxo in new_utxos:
        if (utxo['txid'], utxo['vout']) in existing_utxos_dict:
            # Preserve the existing genesis_txid and sms_txid
            utxo['genesis_txid'] = existing_utxos_dict[(utxo['txid'], utxo['vout'])].get('genesis_txid', utxo['genesis_txid'])
            utxo['sms_txid'] = existing_utxos_dict[(utxo['txid'], utxo['vout'])].get('sms_txid', utxo['sms_txid'])
            utxo['timestamp'] = existing_utxos_dict[(utxo['txid'], utxo['vout'])].get('timestamp', utxo['timestamp'])
            utxo['sender_address'] = existing_utxos_dict[(utxo['txid'], utxo['vout'])].get('sender_address', utxo['sender_address'])
        existing_utxos_dict[(utxo['txid'], utxo['vout'])] = utxo
    merged_utxos = list(existing_utxos_dict.values())

    # Write the merged UTXOs back to the file
    with open(filename, 'w') as f:
        json.dump(merged_utxos, f, indent=4)
    print(f"Created or updated file {filename} with UTXOs for address {address}")

def process_all_wallets(dogecoin_rpc):
    addresses = list_wallet_addresses(dogecoin_rpc)
    for address in addresses:
        print(f"Processing UTXOs for address: {address}")
        process_wallet_utxos(dogecoin_rpc, address)

if __name__ == "__main__":
    dogecoin_rpc = DogecoinRPC(RPC_USER, RPC_PASSWORD, RPC_HOST, RPC_PORT)

    print("\nProcessing all wallets sequentially:")
    process_all_wallets(dogecoin_rpc)
