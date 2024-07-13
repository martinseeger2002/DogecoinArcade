from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal

# Configuration
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.105"
RPC_PORT = 22555

# Connect to Dogecoin node
rpc_url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"
dogecoin_rpc = AuthServiceProxy(rpc_url)

def estimate_fee(num_blocks):
    fee_estimate = dogecoin_rpc.estimatesmartfee(num_blocks)
    if "feerate" in fee_estimate:
        return Decimal(fee_estimate["feerate"])
    else:
        raise Exception("Fee estimation failed")

try:
    # Estimate the fee rate for confirmation within 6 blocks
    fee_rate = estimate_fee(6)
    print(f"Estimated fee rate: {fee_rate} DOGE/kB")
except JSONRPCException as e:
    print(f"An error occurred: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
