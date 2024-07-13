from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Configuration
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.105"
RPC_PORT = 22555

# Function to get RPC connection
def get_rpc_connection():
    rpc_url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"
    return AuthServiceProxy(rpc_url)

# Function to get the input details of a specific input in a transaction
def get_vin_details(txid, vin_index):
    try:
        rpc_connection = get_rpc_connection()
        tx_details = rpc_connection.getrawtransaction(txid, True)
        
        # Get the specified input (vin) details
        if vin_index < len(tx_details['vin']):
            vin = tx_details['vin'][vin_index]
            previous_txid = vin['txid']
            vout_index = vin['vout']
            return (previous_txid, vout_index)
        else:
            print(f"Input index {vin_index} is out of range for transaction {txid}.")
            return None
    except JSONRPCException as e:
        print(f"An error occurred: {e}")
        return None

# Main function
if __name__ == "__main__":
    txid = "b2ebf5ab16aa8b1c8a3d57f378808730621e325c3028064deb1c8b320c056202"
    vin_index = 0  # Define the vin index you want to check
    
    vin_details = get_vin_details(txid, vin_index)
    
    if vin_details:
        previous_txid, vout_index = vin_details
        print(f"VIN details for input {vin_index} of transaction {txid}:")
        print(f"Previous TXID = {previous_txid}, VOUT index = {vout_index}")
    else:
        print(f"No details found for input {vin_index} of transaction {txid}.")
