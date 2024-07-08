from getOrd import process_tx

def main():
    # Placeholder for the genesis_txid
    genesis_txid = "<genesisTXIDhere>"
    
    # Call the process_tx function with the genesis_txid and a depth of 500
    process_tx(genesis_txid, depth=1000)

if __name__ == "__main__":
    main()
