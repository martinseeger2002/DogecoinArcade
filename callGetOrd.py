from getOrdContent import process_tx

def main():
    # Placeholder for the genesis_txid
    genesis_txid = "7d8a721afabbd45403f840c47891648be31e4762833fc725710f0ec1821552a1"
    
    # Call the process_tx function with the genesis_txid and a depth of 500
    process_tx(genesis_txid, depth=1000)

if __name__ == "__main__":
    main()
