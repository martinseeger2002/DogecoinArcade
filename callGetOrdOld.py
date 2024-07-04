from getOrd import process_tx

def main():
    # Placeholder for the genesis_txid
    genesis_txid = "1d0a51706c7ec5bc635620fcd505528ec6d40dd5446a43f027b7182158523451"
    
    # Call the process_tx function with the genesis_txid and a depth of 500
    process_tx(genesis_txid, depth=500)

if __name__ == "__main__":
    main()
