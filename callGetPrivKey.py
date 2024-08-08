import getPrivKey

# Define the wallet address
wallet_address = "DFSQ9DcAghaLZtiVzvidxdCTxpm4Wz7dNQ"

# Get and print the private key
private_key = getPrivKey.get_private_key(wallet_address)
print("Private Key:", private_key)
