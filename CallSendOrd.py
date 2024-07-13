import configparser
from sendOrd import send_ord

# Load RPC credentials from rpc.conf
config = configparser.ConfigParser()
config.read('rpc.conf')

RPC_USER = config.get('rpc', 'user')
RPC_PASSWORD = config.get('rpc', 'password')
RPC_HOST = config.get('rpc', 'host')
RPC_PORT = config.getint('rpc', 'port')

# Transaction variables (user input)
UTXO_TO_SEND_TXID = "1334f5ad579bb5b2a2f59168f6e9d5fb3c60e84d0bd169085c6d3004eaa445dc"  # txid of the UTXO to send
UTXO_TO_SEND_VOUT = 0  # vout of the UTXO to send
RECIPIENT_ADDRESS = "D62YksrgtpLkBWtb2qgfArSpcUncPbXKbA"

# Call the function
send_ord(RPC_USER, RPC_PASSWORD, RPC_HOST, RPC_PORT, UTXO_TO_SEND_TXID, UTXO_TO_SEND_VOUT, RECIPIENT_ADDRESS)
