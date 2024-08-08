import getPubKey

# Define the transaction ID
txid = "58aaf14c5b6b260ef3ca14cf2645baec21dc7e2d3dd4fb580646ca9824f57dc2"

# Get and print the public keys with their associated wallet addresses
pubkeys_with_addresses = getPubKey.get_public_keys_from_tx(txid)
for pubkey, address in pubkeys_with_addresses:
    print(f"Public Key: {pubkey}, Address: {address}")
