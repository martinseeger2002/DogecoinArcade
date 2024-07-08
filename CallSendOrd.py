from sendOrd import send_ord

# Configuration
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.105"
RPC_PORT = 22555

# Transaction variables (user input)
UTXO_TO_SEND_TXID = "c0682f2a153065c36c8d44be803b854cf8c269a73cfd2a7f64f64abd98aa6011"  # txid of the UTXO to send
UTXO_TO_SEND_VOUT = 0  # vout of the UTXO to send
RECIPIENT_ADDRESS = "D5jYAmjRymojMAL2HLZM3n53P3CuPnuBrZ"

# Call the function
send_ord(RPC_USER, RPC_PASSWORD, RPC_HOST, RPC_PORT, UTXO_TO_SEND_TXID, UTXO_TO_SEND_VOUT, RECIPIENT_ADDRESS)
