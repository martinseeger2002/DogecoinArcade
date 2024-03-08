from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from binascii import unhexlify, hexlify
from bitcoin.core.script import CScript

# Configuration
NODE_RPC_HOST = "127.0.0.1:22555"
NODE_RPC_USER = "your_rpc_user"
NODE_RPC_PASS = "veracity31"
TXID = "15f3b73df7e5c072becb1d84191843ba080734805addfccb650929719080f62e"

def extract_data(script_hex):
    script = CScript(unhexlify(script_hex))
    chunks = list(script)

    if len(chunks) < 3 or not isinstance(chunks[0], bytes) or chunks[0].decode() != 'ord':
        raise ValueError('Not a Doginal transaction or invalid script format')

    # Check if the number of pieces is in bytes and convert it
    if isinstance(chunks[1], bytes):
        num_pieces = int.from_bytes(chunks[1], byteorder='little')
    elif isinstance(chunks[1], int):
        num_pieces = chunks[1]
    else:
        raise ValueError('Invalid format for number of pieces')

    if not isinstance(chunks[2], bytes):
        raise ValueError('Content type is not in the expected format')

    content_type = chunks[2].decode()

    data = b''
    for i in range(3, len(chunks), 2):
        if not isinstance(chunks[i + 1], bytes):
            raise ValueError('Data chunk is not in the expected format')
        data += chunks[i + 1]

    return content_type, data

def main():
    try:
        # Construct RPC URL with credentials
        rpc_url = f"http://{NODE_RPC_USER}:{NODE_RPC_PASS}@{NODE_RPC_HOST}"

        # Connect to Dogecoin node via RPC
        rpc_connection = AuthServiceProxy(rpc_url)

        # Retrieve transaction details
        transaction = rpc_connection.getrawtransaction(TXID, 1)
        script_hex = transaction['vin'][0]['scriptSig']['hex']

        # Extract data from transaction
        content_type, data = extract_data(script_hex)

        # Display transaction details and extracted data
        print(f"Transaction Details: {transaction}")
        print(f"Extracted Data: {hexlify(data)}")
        print(f"Content Type: {content_type}")

    except JSONRPCException as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
