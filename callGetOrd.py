from getOrd import process_tx

def main():
    # Placeholder for the genesis_txid
    genesis_txid = "cda93db3e79fffebaaf737051e0bdd614f11f5768bcd4c8a5d9bae0b04b29c3c"
    
    # Call the process_tx function with the genesis_txid and a depth of 500
    process_tx(genesis_txid, depth=1000)

if __name__ == "__main__":
    main()
