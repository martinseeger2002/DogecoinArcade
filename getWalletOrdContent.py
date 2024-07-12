import json
import os
from getOrdContent import process_tx

def file_exists_in_content_folder(file_base_name):
    """Check if a file with the given base name exists in the ./content folder, ignoring the extension."""
    content_folder = "./content"
    for file in os.listdir(content_folder):
        if file.startswith(file_base_name):
            return True
    return False

def process_inscription_id(inscription_id):
    """Process an inscription ID if it doesn't already exist in the content folder."""
    if inscription_id:
        if file_exists_in_content_folder(inscription_id):
            print(f"File for inscriptionId {inscription_id} already exists in the content folder. Skipping.")
        else:
            print(f"Processing inscriptionId: {inscription_id}")
            process_tx(inscription_id, depth=1000)
    else:
        print("Invalid or missing inscriptionId.")

def process_wallet_files():
    folder_path = "./wallets"
    
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist.")
        return

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            print(f"Processing file: {file_path}")
            with open(file_path, 'r') as file:
                data = json.load(file)
            
            for item in data:
                genesis_txid = item.get("genesis_txid")
                if genesis_txid and genesis_txid != "not an ord":
                    process_inscription_id(genesis_txid)
                else:
                    print(f"Skipping genesis_txid {genesis_txid} as it is not an ord.")

if __name__ == "__main__":
    process_wallet_files()
