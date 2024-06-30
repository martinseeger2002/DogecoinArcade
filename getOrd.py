from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import binascii
import mimetypes

# Configuration
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.105"
RPC_PORT = 22555

# Construct the RPC URL
RPC_URL = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"

# Connect to the Dogecoin node
rpc_connection = AuthServiceProxy(RPC_URL)

# Global variable
num_chunks = -1

def hex_to_ascii(hex_string):
    """ Convert hex string to ASCII """
    try:
        ascii_string = binascii.unhexlify(hex_string).decode('ascii')
        return ascii_string
    except Exception as e:
        print(f"Error converting hex to ASCII: {e}")
        return None

def save_to_file(data_string, mime_type, genesis_txid):
    """ Save data string to file with appropriate mime type extension """
    extension = mimetypes.guess_extension(mime_type)
    if not extension:
        extension = '.bin'  # default to binary if mime type is unknown
    filename = f"{genesis_txid}{extension}"
    with open(filename, 'wb') as file:
        file.write(binascii.unhexlify(data_string))

def process_genesis_tx(asm_data):
    """ Process the genesis transaction """
    global num_chunks
    data_string = ""
    num_chunks = int(asm_data[1])
    mime_type_hex = asm_data[2]
    mime_type = hex_to_ascii(mime_type_hex)
    print(f"Mime type: {mime_type}")

    index = 3
    while index < len(asm_data):
        if asm_data[index].isdigit():
            num_chunks = int(asm_data[index])
            data_chunk = asm_data[index + 1]
            print(f"Num_chunks: {num_chunks}, Data_chunk: {data_chunk}")

            data_string += data_chunk
            index += 2

            if num_chunks == 0:
                return data_string, mime_type, True
        else:
            break

    return data_string, mime_type, False

def process_subsequent_tx(asm_data):
    """ Process subsequent transactions """
    global num_chunks
    data_string = ""
    index = 0
    while index < len(asm_data):
        if asm_data[index].isdigit():
            num_chunks = int(asm_data[index])
            data_chunk = asm_data[index + 1]
            print(f"Num_chunks: {num_chunks}, Data_chunk: {data_chunk}")

            data_string += data_chunk
            index += 2

            if num_chunks == 0:
                return data_string, True
        else:
            break

    return data_string, False

def find_next_ordinal_tx(txid, depth):
    try:
        raw_tx = rpc_connection.getrawtransaction(txid, 1)
        block_hash = raw_tx['blockhash']
        block_height = rpc_connection.getblock(block_hash)['height']

        for current_block_height in range(block_height, block_height + depth):
            block_hash = rpc_connection.getblockhash(current_block_height)
            block = rpc_connection.getblock(block_hash, 2)
            for block_tx in block['tx']:
                for vin in block_tx['vin']:
                    if 'txid' in vin and vin['txid'] == txid:
                        return block_tx['txid']
        return None
    except JSONRPCException as e:
        print(f"JSONRPCException while finding next ordinal tx: {e}")
        return None

def process_tx(genesis_txid, depth=10):
    try:
        data_string = ""
        mime_type = None

        is_genesis = True
        txid = genesis_txid

        processed_txids = set()

        while True:
            if txid in processed_txids:
                print("Detected loop, stopping.")
                break
            processed_txids.add(txid)

            raw_tx = rpc_connection.getrawtransaction(txid, 1)

            # Print the transaction ID
            print(f"Transaction ID: {txid}")

            for vin in raw_tx['vin']:
                if 'scriptSig' in vin:
                    asm_data = vin['scriptSig'].get('asm', '').split()

                    if is_genesis:
                        if asm_data[0] == "6582895":
                            new_data_string, mime_type, end_of_data = process_genesis_tx(asm_data)
                            data_string += new_data_string
                            is_genesis = False
                        else:
                            print("Invalid genesis transaction format.")
                            return
                    else:
                        new_data_string, end_of_data = process_subsequent_tx(asm_data)
                        data_string += new_data_string

            # Break if we reached the last chunk
            if end_of_data:
                break

            # Find the next ordinal transaction
            next_txid = find_next_ordinal_tx(txid, depth)
            if next_txid and num_chunks > 0:
                txid = next_txid
            else:
                print(f"End of chain reached, no further ordinals found or num_chunks <= 0.")
                break

        print(f"Data string: {data_string}")

        # Save the compiled data string to a file with appropriate mime type extension
        if mime_type:
            save_to_file(data_string, mime_type, genesis_txid)
        else:
            print("Error: MIME type is None, cannot save file.")

    except JSONRPCException as e:
        print(f"JSONRPCException: {e}")  # Handle exceptions as needed
    except Exception as e:
        print(f"Unexpected error: {e}")

# Example usage
genesis_txid = "28e222a31f5195a71933b306412fe5b2f039390e3876586674d2f047761a7e29"
process_tx(genesis_txid, depth=500)  # Start with a depth of 500 blocks
