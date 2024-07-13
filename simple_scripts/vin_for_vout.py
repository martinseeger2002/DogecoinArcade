from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal

# Configuration
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.105"
RPC_PORT = 22555

# Connect to the Dogecoin node
rpc_connection = AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}")

def get_transaction_details(txid):
    try:
        return rpc_connection.getrawtransaction(txid, True)
    except JSONRPCException as e:
        print(f"An error occurred: {e}")
        return None

# Function to fetch previous transaction outputs
def get_previous_tx_output(txid, vout):
    try:
        prev_tx = rpc_connection.getrawtransaction(txid, True)
        return prev_tx['vout'][vout]
    except JSONRPCException as e:
        print(f"An error occurred: {e}")
        return None

def find_corresponding_vins(txid, target_vout_index):
    transaction = get_transaction_details(txid)
    if not transaction:
        return None

    vins = transaction['vin']
    vouts = transaction['vout']

    # Get the value of each vin
    vin_values = []
    for vin in vins:
        prev_tx_output = get_previous_tx_output(vin['txid'], vin['vout'])
        if prev_tx_output:
            vin_values.append(prev_tx_output['value'])
        else:
            vin_values.append(Decimal('0'))

    # Track remaining value of each vin
    vin_remaining_values = vin_values[:]
    corresponding_vins_list = []

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

        corresponding_vins_list.append(corresponding_vins)

    # Return the corresponding vins for the specified vout index
    if target_vout_index < len(corresponding_vins_list):
        return corresponding_vins_list[target_vout_index]
    else:
        print("Invalid vout index")
        return None

# Define the transaction ID and the vout index you are interested in
txid = "22f898c81706b582b350f8d31b9b86c0d0c6baaeeee03590250a16eeaa8ed480"
vout_index = 0  # Change this to the desired vout index

# Get the corresponding vin(s) for the specified vout
corresponding_vins = find_corresponding_vins(txid, vout_index)
if corresponding_vins is not None:
    print(f"Corresponding Vin Index(es) for Vout Index {vout_index}:")
    for vin_index in corresponding_vins:
        print(vin_index)
else:
    print("No corresponding Vin found.")
