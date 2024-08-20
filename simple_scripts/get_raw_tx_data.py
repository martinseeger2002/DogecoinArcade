from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal

# Configuration
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.84"
RPC_PORT = 22555

# Connect to the Dogecoin node
rpc_connection = AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}")

# Transaction ID
txid = "64cea590672a5cf15d10acd1352c62d3d009603422134fd7c8757a3c0b49aec2"

def get_previous_tx_output(txid, vout):
    try:
        prev_tx = rpc_connection.getrawtransaction(txid, True)
        return prev_tx['vout'][vout]
    except JSONRPCException as e:
        print(f"An error occurred: {e}")
        return None

def decode_script(script_hex):
    try:
        decoded_script = rpc_connection.decodescript(script_hex)
        return decoded_script.get("asm", "N/A")
    except JSONRPCException as e:
        print(f"An error occurred: {e}")
        return "N/A"

def save_transaction_inputs_to_file(txid):
    try:
        # Fetch the raw transaction data in decoded format
        transaction = rpc_connection.getrawtransaction(txid, True)

        # Prepare the content to be saved
        file_content = f"Transaction ID: {txid}\n"
        file_content += "Inputs:\n"

        vins = transaction['vin']
        for index, vin in enumerate(vins):
            prev_txid = vin['txid']
            prev_vout = vin['vout']
            prev_output = get_previous_tx_output(prev_txid, prev_vout)

            if prev_output:
                value = prev_output['value']
                script_pub_key = prev_output['scriptPubKey']
                addresses = script_pub_key.get('addresses', ["N/A"])
                script_sig_hex = vin.get('scriptSig', {}).get('hex', '')
                script_sig_asm = decode_script(script_sig_hex)

                file_content += f"  Input {index + 1}:\n"
                file_content += f"    Previous Transaction ID: {prev_txid}\n"
                file_content += f"    Output Index: {prev_vout}\n"
                file_content += f"    Value: {Decimal(value)} DOGE\n"
                file_content += f"    Addresses: {', '.join(addresses)}\n"
                file_content += f"    ScriptSig (Hex): {script_sig_hex}\n"
                file_content += f"    ScriptSig (ASM): {script_sig_asm}\n"
            else:
                file_content += f"  Input {index + 1}:\n"
                file_content += f"    Previous Transaction ID: {prev_txid}\n"
                file_content += f"    Output Index: {prev_vout}\n"
                file_content += "    Value: N/A (error fetching data)\n"
                file_content += "    Addresses: N/A\n"
                file_content += "    ScriptSig (Hex): N/A\n"
                file_content += "    ScriptSig (ASM): N/A\n"

        # Save the input details to a file named <txid>.txt
        with open(f"{txid}.txt", "w") as file:
            file.write(file_content)

        print(f"Transaction inputs saved to {txid}.txt")

    except JSONRPCException as e:
        print(f"An error occurred: {e}")

# Save the transaction inputs to a file
save_transaction_inputs_to_file(txid)
