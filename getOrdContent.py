import configparser
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import binascii
import mimetypes
import os
from tqdm import tqdm

# Load RPC credentials from rpc.conf
config = configparser.ConfigParser()
config.read('rpc.conf')

RPC_USER = config.get('rpc', 'user')
RPC_PASSWORD = config.get('rpc', 'password')
RPC_HOST = config.get('rpc', 'host')
RPC_PORT = config.getint('rpc', 'port')

# Construct the RPC URL
RPC_URL = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"

# Connect to the Dogecoin node
rpc_connection = AuthServiceProxy(RPC_URL)

# Global variable
num_chunks = -1
progress_bar = None

def hex_to_ascii(hex_string):
    """ Convert hex string to ASCII """
    try:
        ascii_string = binascii.unhexlify(hex_string).decode('ascii')
        return ascii_string
    except Exception as e:
        return None

def save_to_file(data_string, mime_type, genesis_txid):
    """ Save data string to file with appropriate mime type extension """
    if ';' in mime_type:
        mime_type = mime_type.split(';')[0].strip()
    
    extension = '.bin'  # default to binary if mime type is unknown
    
    if mime_type == 'image/webp':
        extension = '.webp'
    else:
        guessed_extension = mimetypes.guess_extension(mime_type)
        if guessed_extension:
            extension = guessed_extension
    
    output_dir = './content/'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.join(output_dir, f"{genesis_txid}{extension}")
    try:
        with open(filename, 'wb') as file:
            file.write(binascii.unhexlify(data_string))
    except Exception as e:
        pass

def process_genesis_tx(asm_data):
    """ Process the genesis transaction """
    global num_chunks, progress_bar
    data_string = ""
    num_chunks = int(asm_data[1])
    mime_type_hex = asm_data[2]
    mime_type = hex_to_ascii(mime_type_hex)

    progress_bar = tqdm(total=num_chunks, desc="Processing chunks", unit="chunk")

    index = 3
    while index < len(asm_data):
        if asm_data[index].isdigit():
            num_chunks = int(asm_data[index])
            data_chunk = asm_data[index + 1]

            data_string += data_chunk
            index += 2

            progress_bar.update(1)

            if num_chunks == 0:
                return data_string, mime_type, True
        else:
            break

    return data_string, mime_type, False

def process_subsequent_tx(asm_data):
    """ Process subsequent transactions """
    global num_chunks, progress_bar
    data_string = ""
    index = 0
    while index < len(asm_data):
        if asm_data[index].isdigit():
            num_chunks = int(asm_data[index])
            data_chunk = asm_data[index + 1]

            data_string += data_chunk
            index += 2

            if progress_bar:
                progress_bar.update(1)

            if num_chunks == 0:
                return data_string, True
        else:
            break

    return data_string, False

def get_vin_details(txid, vin_index):
    """ Get the input details of a specific input in a transaction """
    try:
        tx_details = rpc_connection.getrawtransaction(txid, True)
        if vin_index < len(tx_details['vin']):
            vin = tx_details['vin'][vin_index]
            previous_txid = vin['txid']
            vout_index = vin['vout']
            return previous_txid, vout_index
        else:
            return None
    except JSONRPCException as e:
        return None

def find_next_ordinal_tx(txid, vout_index, depth, genesis_txid):
    try:
        raw_tx = rpc_connection.getrawtransaction(txid, 1)
        block_hash = raw_tx['blockhash']
        block_height = rpc_connection.getblock(block_hash)['height']

        index_file_path = f"./indexes/{genesis_txid}.txt"
        os.makedirs(os.path.dirname(index_file_path), exist_ok=True)

        for current_block_height in range(block_height, block_height + depth):
            block_hash = rpc_connection.getblockhash(current_block_height)
            block = rpc_connection.getblock(block_hash, 2)
            for block_tx in block['tx']:
                for vin in block_tx['vin']:
                    if 'txid' in vin and vin['txid'] == txid and vin['vout'] == vout_index:
                        next_txid = block_tx['txid']
                        with open(index_file_path, 'a') as file:
                            file.write(next_txid + '\n')
                        return next_txid, vin['vout']
        return None, None
    except JSONRPCException as e:
        return None, None

def read_txids_from_file(genesis_txid):
    """ Read the list of transaction IDs from a file """
    filename = f"./indexes/{genesis_txid}.txt"
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            txid_list = file.read().splitlines()
        return txid_list
    else:
        return None

def create_index_file(genesis_txid):
    """ Create an empty index file for the genesis transaction """
    index_file_path = f"./indexes/{genesis_txid}.txt"
    os.makedirs(os.path.dirname(index_file_path), exist_ok=True)
    if not os.path.exists(index_file_path):
        with open(index_file_path, 'w') as file:
            file.write('')

def process_tx(genesis_txid, depth=10):
    global progress_bar
    try:
        data_string = ""
        mime_type = None

        is_genesis = True
        txid = genesis_txid

        processed_txids = set()
        vout_index = 0

        # Create the index file as soon as we start processing the genesis transaction
        create_index_file(genesis_txid)

        txid_list = read_txids_from_file(genesis_txid)
        if not txid_list:
            txid_list = []

        while True:
            if txid in processed_txids:
                # Move on to the next transaction in the list
                if txid_list:
                    txid = txid_list.pop(0)
                    vout_index = 0
                    continue
                else:
                    break
            processed_txids.add(txid)

            raw_tx = rpc_connection.getrawtransaction(txid, 1)

            for vin in raw_tx['vin']:
                if 'scriptSig' in vin:
                    asm_data = vin['scriptSig'].get('asm', '').split()

                    if is_genesis:
                        if asm_data[0] == "6582895":
                            new_data_string, mime_type, end_of_data = process_genesis_tx(asm_data)
                            data_string += new_data_string
                            is_genesis = False
                        else:
                            return
                    else:
                        new_data_string, end_of_data = process_subsequent_tx(asm_data)
                        data_string += new_data_string

                    if progress_bar:
                        progress_bar.update(1)

            if end_of_data:
                break

            if num_chunks > 0:
                if txid_list:
                    txid = txid_list.pop(0)
                    vout_index = 0
                else:
                    next_txid, vout_index = find_next_ordinal_tx(txid, vout_index, depth, genesis_txid)
                    if next_txid:
                        txid = next_txid
                    else:
                        break
            else:
                break

        if len(data_string) % 2 != 0:
            data_string += "00000"

        if mime_type:
            save_to_file(data_string, mime_type, genesis_txid)
        else:
            pass

        if progress_bar:
            progress_bar.close()

    except JSONRPCException as e:
        pass
    except Exception as e:
        pass

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <genesis_txid>")
    else:
        genesis_txid = sys.argv[1]
        process_tx(genesis_txid, depth=500)
