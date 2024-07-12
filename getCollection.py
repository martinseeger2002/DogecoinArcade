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
    if inscription_id and inscription_id.endswith('i0'):
        inscription_id = inscription_id[:-2]  # Remove the 'i0' from the end
        if file_exists_in_content_folder(inscription_id):
            print(f"File for inscriptionId {inscription_id} already exists in the content folder. Skipping.")
        else:
            print(f"Processing inscriptionId: {inscription_id}")
            process_tx(inscription_id, depth=1000)
            return 1  # Return 1 for a successfully processed UTXO
    else:
        print("Invalid or missing inscriptionId.")
    return 0  # Return 0 if nothing was processed

def load_scanned_collections():
    """Load the scanned collections from the JSON file."""
    scanned_collections_path = "./data/scanned_collections.json"
    if not os.path.exists(scanned_collections_path):
        return {}
    with open(scanned_collections_path, 'r') as file:
        return json.load(file)

def save_scanned_collections(scanned_collections):
    """Save the scanned collections to the JSON file."""
    os.makedirs("./data", exist_ok=True)
    scanned_collections_path = "./data/scanned_collections.json"
    with open(scanned_collections_path, 'w') as file:
        json.dump(scanned_collections, file, indent=4)

def get_collection(file_name):
    folder_path = "./collections"
    file_path = os.path.join(folder_path, file_name)
    
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return
    
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    collection = data.get("collection", {})
    items = data.get("items", [])
    collection_name = collection.get("name", "Unnamed Collection")
    
    scanned_collections = load_scanned_collections()

    if collection_name in scanned_collections:
        print(f"Collection '{collection_name}' has already been scanned. Skipping.")
        return

    print(f"Processing collection: {collection_name}")
    
    # Process the thumbnail txid
    thumbnail_inscription_id = collection.get("thumbnail")
    scanned_utxos = 0
    
    if thumbnail_inscription_id:
        print("Processing thumbnail inscription ID.")
        scanned_utxos += process_inscription_id(thumbnail_inscription_id)
    
    for item in items:
        inscription_id = item.get("inscriptionId")
        scanned_utxos += process_inscription_id(inscription_id)
    
    # Save the scanned collection
    scanned_collections[collection_name] = scanned_utxos
    save_scanned_collections(scanned_collections)
    print(f"Scanned {scanned_utxos} UTXOs for collection '{collection_name}'.")

if __name__ == "__main__":
    # Example usage
    file_name = "your_collection_file.json"
    get_collection(file_name)
