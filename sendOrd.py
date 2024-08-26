import json
import os
import configparser
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal, ROUND_DOWN

def send_ord(utxo_txid, utxo_vout, recipient_address, wallets_dir="./wallets"):
    # Load RPC credentials from rpc.conf
    config = configparser.ConfigParser()
    config.read('rpc.conf')

    def get_rpc_connection(address):
        if address.startswith('D'):
            rpc_section = 'dogecoin_rpc'
        elif address.startswith('be'):
            rpc_section = 'bellscoin_rpc'
        else:
            raise ValueError("Unsupported address format")

        rpc_user = config.get(rpc_section, 'user')
        rpc_password = config.get(rpc_section, 'password')
        rpc_host = config.get(rpc_section, 'host')
        rpc_port = config.getint(rpc_section, 'port')

        rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"
        return AuthServiceProxy(rpc_url)

    def estimate_fee(rpc_connection, num_blocks):
        fee_estimate = rpc_connection.estimatesmartfee(num_blocks)
        if "feerate" in fee_estimate:
            return Decimal(fee_estimate["feerate"])
        else:
            raise Exception("Fee estimation failed")

    def get_utxos_from_wallet(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    def select_utxos_for_fee(utxos, amount_needed):
        sorted_utxos = sorted(utxos, key=lambda x: x['amount'])
        selected_utxos = []
        total_amount = Decimal('0')
        for utxo in sorted_utxos:
            if utxo['genesis_txid'] == 'not an ord':
                selected_utxos.append(utxo)
                total_amount += Decimal(utxo['amount'])
            if total_amount >= amount_needed:
                break
        return selected_utxos, total_amount

    try:
        # Determine which RPC to use based on the recipient address
        rpc_connection = get_rpc_connection(recipient_address)

        # Step 1: Read UTXO data from all JSON files in the wallets directory
        wallet_files = [os.path.join(wallets_dir, file) for file in os.listdir(wallets_dir) if file.endswith('.json')]
        wallet_utxos = {}
        utxo_to_send = None
        sending_wallet_address = None

        for wallet_file in wallet_files:
            utxos = get_utxos_from_wallet(wallet_file)
            wallet_utxos[wallet_file] = utxos
            # Find the UTXO to send
            utxo_to_send = next((utxo for utxo in utxos if utxo['txid'] == utxo_txid and utxo['vout'] == utxo_vout), None)
            if utxo_to_send:
                sending_wallet_address = os.path.splitext(os.path.basename(wallet_file))[0]
                break

        if not utxo_to_send:
            raise Exception("UTXO to send not found in any wallet")

        # Step 2: Estimate the fee rate
        fee_rate = estimate_fee(rpc_connection, 3)  # Estimate fee for confirmation within 4 blocks
        print(f"Estimated fee rate: {fee_rate} COIN/kB")

        # Calculate the transaction size in bytes (approximation)
        tx_size = Decimal(250)  # This is an approximation. Adjust as necessary.

        # Calculate the transaction fee
        fee = (fee_rate * (tx_size / Decimal(1000))).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
        print(f"Calculated transaction fee: {fee} COIN")

        # Step 3: Select UTXOs for the fee from the same wallet
        remaining_utxos = [utxo for utxo in wallet_utxos[os.path.join(wallets_dir, f"{sending_wallet_address}.json")] if not (utxo['txid'] == utxo_txid and utxo['vout'] == utxo_vout)]
        fee_utxos, total_fee_amount = select_utxos_for_fee(remaining_utxos, fee)

        if total_fee_amount < fee:
            raise Exception("Not enough UTXOs to cover the fee")

        # Calculate the change amount
        change_amount = (total_fee_amount - fee).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
        print(f"Change amount: {change_amount} COIN")

        # Define the inputs
        inputs = [{"txid": utxo['txid'], "vout": utxo['vout']} for utxo in fee_utxos]
        # Include the UTXO to send as vin[0]
        inputs.insert(0, {"txid": utxo_to_send['txid'], "vout": utxo_to_send['vout']})

        # Define the outputs
        outputs = {
            recipient_address: float(utxo_to_send['amount']),
        }
        if change_amount > Decimal('0'):
            outputs[sending_wallet_address] = float(change_amount)

        # Ensure the UTXO to send is the first output
        outputs = {recipient_address: float(utxo_to_send['amount']), **outputs}

        # Step 4: Create the raw transaction
        raw_tx = rpc_connection.createrawtransaction(inputs, outputs)

        # Step 5: Sign the raw transaction
        signed_tx = rpc_connection.signrawtransaction(raw_tx)

        # Step 6: Send the raw transaction
        txid = rpc_connection.sendrawtransaction(signed_tx["hex"])

        print(f"Transaction sent with txid: {txid}")

    except JSONRPCException as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Transaction variables (user input)
UTXO_TO_SEND_TXID = "1334f5ad579bb5b2a2f59168f6e9d5fb3c60e84d0bd169085c6d3004eaa445dc"  # txid of the UTXO to send
UTXO_TO_SEND_VOUT = 0  # vout of the UTXO to send
RECIPIENT_ADDRESS = "D62YksrgtpLkBWtb2qgfArSpcUncPbXKbA"

try:
    # Call the function
    send_ord(UTXO_TO_SEND_TXID, UTXO_TO_SEND_VOUT, RECIPIENT_ADDRESS)

except ValueError as e:
    print(f"Error: {e}")
except configparser.Error as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")