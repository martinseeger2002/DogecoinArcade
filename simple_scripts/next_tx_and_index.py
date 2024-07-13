from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal

# Configuration
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.105"
RPC_PORT = 22555

# Connect to the Dogecoin node
rpc_connection = AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}")

# Transaction ID and specific output index to inspect
txid = "4516096745d62b05fda649fd8037b333a2707a74b5e222416c8b59e4a9e7f00d"
output_index = 0

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
vin_details = []
for vin in vins:
    prev_tx_output = get_previous_tx_output(vin['txid'], vin['vout'])
    if prev_tx_output:
        vin_values.append(prev_tx_output['value'])
        vin_details.append((vin['txid'], vin['vout']))
    else:
        vin_values.append(Decimal('0'))
        vin_details.append((vin['txid'], vin['vout']))

# Track remaining value of each vin
vin_remaining_values = vin_values[:]

# Process all vouts but only store the information for the specific output_index
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

# Print the information for the chosen vout index
if chosen_vout_info:
    if chosen_vout_info['corresponding_vins']:
        for vin_index in chosen_vout_info['corresponding_vins']:
            vin_txid, vout_idx = vin_details[vin_index]
            print(f"Previous TXID: {vin_txid}, VOUT Index: {vout_idx}")
else:
    print(f"Output index {output_index} is out of range.")
