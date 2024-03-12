GitHub Repository: Dogecoin Data Extraction and Assembly Tool
Overview
This repository contains a Python-based tool for extracting and assembling data from Dogecoin transactions. The tool is primarily focused on processing transaction details from a Dogecoin node, extracting specific pieces of data from these transactions, and then assembling this data into a coherent file format based on the MIME type.

Files in the Repository
assemble_data.py: Contains functions for processing a text file containing Dogecoin transaction data, splitting this data into parts, assembling it into a hex string, and then converting this string into a file of an appropriate type based on its MIME type.
dogecoin_transaction_details.py: This script connects to a Dogecoin node using RPC (Remote Procedure Call) and retrieves transaction details based on a given transaction ID (TXID).
main.py: The main script that uses the functionalities of the other two scripts. It extracts 'scriptSig' data from transactions, looks for a specific sequence in these transactions, and saves the relevant data into a file.
Features
Extract Transaction Details: Connects to a Dogecoin node and extracts details from specific transactions.
Data Processing: Processes the extracted data to find specific sequences and splits the data into manageable parts.
File Assembly: Reconstructs the processed data into a coherent format and saves it into a file, the type of which is determined based on its MIME type.
How to Use
Setup Node Connection: Configure the Dogecoin node connection settings in main.py (RPC host, user, and password).
Run main.py: Execute main.py. This script will use the other two scripts to extract data from transactions and assemble it into a file.
Check Output: The output will be saved in a file whose path is printed to the console.
Prerequisites
Python 3.x
Access to a Dogecoin node with RPC enabled.
Required Python packages: bitcoinrpc.
Installation
Clone the repository.
Install the required Python package using pip install python-bitcoinRPC.
Ensure you have access to a Dogecoin node with RPC enabled and configured.
Configuration
Set the following parameters in main.py:

NODE_RPC_HOST: Hostname and port of the Dogecoin node.
NODE_RPC_USER: RPC user.
NODE_RPC_PASS: RPC password.
