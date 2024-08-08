from getSmsContent import process_tx

def main():
    # Placeholder for the genesis_txid
    genesis_txid = "58aaf14c5b6b260ef3ca14cf2645baec21dc7e2d3dd4fb580646ca9824f57dc2"
    
    # Call the process_tx function with the genesis_txid and a depth of 500
    process_tx(genesis_txid, depth=1000)

if __name__ == "__main__":
    main()
