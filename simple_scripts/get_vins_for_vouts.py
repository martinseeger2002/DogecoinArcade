from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal

# Configuration
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.105"
RPC_PORT = 22555

# Connect to the Dogecoin node
rpc_connection = AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}")

# Transaction ID
txid = "92d6c7c6ec4ee1179010172547f4d2e6df20df9119d2e4135a883b6df1e83ec5"

# Fetch the transaction details
try:
    transaction = rpc_connection.getrawtransaction(txid, True)
except JSONRPCException as e:
    print(f"An error occurred: {e}")
    exit(1)

# Extract vin and vout
vins = transaction['vin']
vouts = transaction['vout']

# Function to fetch previous transaction outputs
def get_previous_tx_output(txid, vout):
    try:
        prev_tx = rpc_connection.getrawtransaction(txid, True)
        return prev_tx['vout'][vout]
    except JSONRPCException as e:
        print(f"An error occurred: {e}")
        return None

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

# Display the vouts followed by their corresponding vins
for vout_index, vout in enumerate(vouts):
    print(f"Vout Index: {vout_index} (Value: {vout['value']}):")
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
    
    if corresponding_vins:
        print("Corresponding Vin Index(es):")
        for vin_index in corresponding_vins:
            print(vin_index)
    else:
        print("No corresponding Vin found.")
    print("-")
