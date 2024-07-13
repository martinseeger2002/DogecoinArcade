##This get_vouts_for_vins.py connects to a Dogecoin node using RPC credentials to retrieve and display the input details of a specified transaction. Specifically, it fetches and prints the previous transaction IDs (txid) and the corresponding output indices (vout) that were used as inputs in the current transaction (vin). This helps in tracing the source of each input used in a transaction, providing insights into the transaction's history and flow of funds.

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

# Function to get the input details of a transaction
def get_vin_indices(txid):
    try:
        rpc_connection = get_rpc_connection()
        tx_details = rpc_connection.getrawtransaction(txid, True)
        
        # List to hold (previous_txid, vout_index) tuples
        vin_indices = []

        # Iterate over all inputs (vins) in the transaction
        for vin in tx_details['vin']:
            previous_txid = vin['txid']
            vout_index = vin['vout']
            vin_indices.append((previous_txid, vout_index))
        
        return vin_indices
    except JSONRPCException as e:
        print(f"An error occurred: {e}")
        return []

# Main function
if __name__ == "__main__":
    txid = "92d6c7c6ec4ee1179010172547f4d2e6df20df9119d2e4135a883b6df1e83ec5"
    vin_indices = get_vin_indices(txid)
    
    if vin_indices:
        print(f"VIN indices for transaction {txid}:")
        for idx, (vin_txid, vout) in enumerate(vin_indices):
            print(f"Input {idx}: Previous TXID = {vin_txid}, VOUT index = {vout}")
    else:
        print(f"No inputs found for transaction {txid}.")
