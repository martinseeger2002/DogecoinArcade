import json
import os
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal, ROUND_DOWN

def send_ord(rpc_user, rpc_password, rpc_host, rpc_port, utxo_txid, utxo_vout, recipient_address, wallets_dir="./wallets"):
    # Connect to Dogecoin node
    rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"
    dogecoin_rpc = AuthServiceProxy(rpc_url)

    def estimate_fee(num_blocks):
        fee_estimate = dogecoin_rpc.estimatesmartfee(num_blocks)
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
        fee_rate = estimate_fee(3)  # Estimate fee for confirmation within 4 blocks
        print(f"Estimated fee rate: {fee_rate} DOGE/kB")

        # Calculate the transaction size in bytes (approximation)
        tx_size = Decimal(250)  # This is an approximation. Adjust as necessary.

        # Calculate the transaction fee
        fee = (fee_rate * (tx_size / Decimal(1000))).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
        print(f"Calculated transaction fee: {fee} DOGE")

        # Step 3: Select UTXOs for the fee from the same wallet
        remaining_utxos = [utxo for utxo in wallet_utxos[os.path.join(wallets_dir, f"{sending_wallet_address}.json")] if not (utxo['txid'] == utxo_txid and utxo['vout'] == utxo_vout)]
        fee_utxos, total_fee_amount = select_utxos_for_fee(remaining_utxos, fee)

        if total_fee_amount < fee:
            raise Exception("Not enough UTXOs to cover the fee")

        # Calculate the change amount
        change_amount = (total_fee_amount - fee).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
        print(f"Change amount: {change_amount} DOGE")

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
        raw_tx = dogecoin_rpc.createrawtransaction(inputs, outputs)

        # Step 5: Sign the raw transaction
        signed_tx = dogecoin_rpc.signrawtransaction(raw_tx)

        # Step 6: Send the raw transaction
        txid = dogecoin_rpc.sendrawtransaction(signed_tx["hex"])

        print(f"Transaction sent with txid: {txid}")

    except JSONRPCException as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


