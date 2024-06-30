
# Dogecoin Ordinal Data Extractor

This script extracts data from Dogecoin ordinal transactions and compiles it into a file. It processes a genesis transaction and subsequent transactions to reconstruct the original data.

## Prerequisites

1. **Python 3.6+**
2. **BitcoinRPC Library**:
   Install the `python-bitcoinlRPC` library using:
   ```sh
   pip install python-bitcoinRPC
   ```
3. **Dogecoin Node**:
   Ensure you have a running Dogecoin node with RPC enabled. 

## Configuration

1. **RPC Configuration**:
   Update the following configuration in the script with your Dogecoin node's RPC credentials:
   ```python
   RPC_USER = "your_rpc_user"
   RPC_PASSWORD = "your_rpc_password"
   RPC_HOST = "192.168.68.105"
   RPC_PORT = 22555
   ```

## How to Use

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/your-repo/dogecoin-ordinal-extractor.git
   cd dogecoin-ordinal-extractor
   ```

2. **Run the Script**:
   Modify the `genesis_txid` variable in the script to the genesis transaction ID you want to process, and run the script:
   ```python
   genesis_txid = "your_genesis_txid"
   process_tx(genesis_txid, depth=10)  # Adjust depth as needed
   ```

## Script Description

### Functions

1. **hex_to_ascii(hex_string)**:
   Converts a hexadecimal string to an ASCII string.

2. **save_to_file(data_string, mime_type, genesis_txid)**:
   Saves the compiled data string to a file with the appropriate MIME type extension.

3. **process_genesis_tx(asm_data)**:
   Processes the genesis transaction and extracts the initial data chunks and MIME type.

4. **process_subsequent_tx(asm_data)**:
   Processes subsequent transactions to extract data chunks.

5. **find_next_ordinal_tx(txid, depth)**:
   Finds the next ordinal transaction ID by scanning the blockchain within the specified depth.

6. **process_tx(genesis_txid, depth=10)**:
   Main function to process the genesis transaction and subsequent transactions to compile the data string and save it to a file.

### Example Usage

Modify the `genesis_txid` variable in the script with the genesis transaction ID you want to process and run the script:
```sh
python getOrd.py
```

### Output

The script will print the MIME type and data chunks while processing. Once it compiles the entire data, it saves the data to a file with the name being the genesis transaction ID and the appropriate file extension.

## Error Handling

The script handles JSON-RPC exceptions and conversion errors. If any unexpected error occurs, it will print the error message and stop further processing.

---

Feel free to reach out for any further assistance or queries!
