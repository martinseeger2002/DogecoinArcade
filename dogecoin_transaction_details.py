# dogecoin_transaction_details.py

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

def get_transaction_details(txid, rpc_user, rpc_pass, rpc_host):
    try:
        # Construct RPC URL with credentials
        rpc_url = f"http://{rpc_user}:{rpc_pass}@{rpc_host}"

        # Connect to Dogecoin node via RPC
        rpc_connection = AuthServiceProxy(rpc_url)

        # Retrieve transaction details
        transaction = rpc_connection.getrawtransaction(txid, 1)

        # Extract and print the 'asm' field from 'scriptSig'
        script_sig_asm = transaction['vin'][0]['scriptSig']['asm']
        details = f"'scriptSig': {{'asm': '{script_sig_asm}'}}\n"

        # Print input TXID (from vin)
        input_txids = [vin['txid'] for vin in transaction['vin']]
        details += f"Input TXIDs: {input_txids}\n"

        # Print output TXIDs (from vout)
        output_txids = [f"{txid}:{vout['n']}" for vout in transaction['vout']]
        details += f"Output TXIDs: {output_txids}\n"

        return details

    except JSONRPCException as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"