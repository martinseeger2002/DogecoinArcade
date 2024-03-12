from assemble_data import process_file, save_data_as_hex_txt, save_file_as_file
import dogecoin_transaction_details as dt

# Configuration
NODE_RPC_HOST = "127.0.0.1:22555"
NODE_RPC_USER = "your_rpc_user"
NODE_RPC_PASS = "your_rpc_pass"
TXID = "f32ddc0bf29d46ef2460dc8e7dc071790237195160e294a462cdeb698f146f3d"

scriptSig_list = []  # Initialize the list to store 'scriptSig' data


def extract_data():
    global TXID  # Declare TXID as global to modify it within the function

    while True:
        transaction_details = dt.get_transaction_details(TXID, NODE_RPC_USER, NODE_RPC_PASS, NODE_RPC_HOST)
        print(f"Checking for '6582895' in {TXID}")
        start = transaction_details.find("'scriptSig': {'asm': '") + len("'scriptSig': {'asm': '")
        end = transaction_details.find("'}", start)
        if start > len("'scriptSig': {'asm': '") - 1 and end != -1:
            scriptSig_asm = transaction_details[start:end]
            scriptSig_list.append(scriptSig_asm)
        else:
            print("scriptSig data not found in the transaction details.")
        if "6582895" in transaction_details:
            print(f"TXID containing '6582895': {TXID}")
            with open('temp_scriptSig_list.txt', 'w') as file:
                file.write(' '.join(scriptSig_list))
                
            break

        # Extract input TXID from the transaction details
        start = transaction_details.find("Input TXIDs: [") + len("Input TXIDs: [")
        end = transaction_details.find("]", start)
        input_txids = transaction_details[start:end].replace("'", "").split(", ")

        # Check if there are input TXIDs to follow, if not, break the loop
        if not input_txids or input_txids[0] == '':
            print("No further input TXIDs to follow. Exiting.")
            break

        # Update TXID to the first input TXID and repeat
        TXID = input_txids[0]

if __name__ == "__main__":
    extract_data()
    # Path to your input file
    file_path = 'temp_scriptSig_list.txt'

    # Process the file
    num_chunks, file_parts, MIME_type = process_file(file_path)

    # Save data as a hex string in a text file
    #hex_file_path = save_data_as_hex_txt(num_chunks, file_parts)
    #print(f"Data saved as hex in file: {hex_file_path}")

    # Convert and save the data as a file of the appropriate type
    file_path = save_file_as_file(num_chunks, file_parts, MIME_type)
    print(f"Data saved in file: {file_path}")
