
# Dogecoin Arcade Project

This project is a comprehensive system for managing and interacting with Dogecoin and Bellscoin ordinals, including tools for collection management, content handling, blockchain interaction, and SMS functionality. Below is a detailed overview of the project structure and components.

## Project Structure

### Folders

- **collections**: Contains JSON files defining various collections, each with metadata and associated items.
- **content**: Stores ordinal content files, named after their genesis ordinal transaction IDs.
- **files**: Contains additional project files (added 2 weeks ago).
- **indexes**: Holds index text files for each ordinal, containing subsequent transaction IDs for multi-transaction ordinals.
- **jsonTools**: Contains a program for processing `DM.json` files to output Dogecoin Arcade collection JSONs.
- **simple_scripts**: A collection of tools for viewing transaction data and interacting with the blockchain.
- **sms**: Contains `addressBook.json` and other SMS-related files.
- **static**: Stores non-ordinal content files.
- **templates**: Contains non-ordinal HTML files and JavaScript code for Dogecoin Arcade.

### Key Files

- **CallGetCollection.py**: Retrieves ordinal data for a collection and saves it to the `content` folder.
- **CallSendOrd.py**: Sends an ordinal using `sendOrd` with specified parameters. Now includes Bellscoin cross-chain capabilities.
- **DecryptSmsData.py**: Decrypts SMS data (updated to use `.smswallet` extension).
- **DogecoinArcade.py**: Flask server for serving ordinal content.
- **DogecoinArcadeAPI.py**: API endpoints for various functionalities.
- **SendSms.py**: Sends encrypted SMS messages and logs transactions.
- **callDecryptData.py**: Calls the decryption function for data.
- **callGetOrd.py**: Retrieves data for a specific ordinal.
- **callGetPrivKey.py**: Retrieves private keys (SMS functionality added).
- **callGetPubKey.py**: Retrieves public keys (SMS functionality added).
- **callGetSms.py**: Retrieves SMS data.
- **decryptData.py** and **decrypt_data.py**: Decryption utilities.
- **decryptWalletSmsContent.py**: Decrypts wallet SMS content (fixed PK bug).
- **encrypt_data.py**: Encryption utility for SMS.
- **eraseContent.py** and **eraseIndexes.py**: Utilities to delete content and index files below a size threshold.
- **getCollection.py**: Retrieves ordinal data for collection JSONs.
- **getHDSingleWalletKeys.py**: Generates HD wallet keys.
- **getOrdContent.py**: Extracts and saves ordinal content data. Now supports Bellscoin.
- **getPrivKey.py** and **getPubKey.py**: Retrieve private and public keys. Now support Bellscoin.
- **getSmsContent.py**: Retrieves SMS content. Now supports Bellscoin.
- **getWalletOrdContent.py**: Retrieves all ordinals from wallet JSONs.
- **getWalletSmsContent.py**: Retrieves SMS-related ordinals from wallet JSONs.
- **rpc.conf**: Contains RPC credentials for Dogecoin and Bellscoin.
- **sendOrd.py**: Sends an ordinal. Now supports Bellscoin.
- **sendsms.js**: JavaScript utility for sending SMS (updated to use `.smswallet.json`).
- **walletSync.py**: Creates and updates wallet JSON files. Now includes Bellscoin RPC.

## Features

1. **Ordinal Management**: Process, retrieve, and manage Dogecoin and Bellscoin ordinals.
2. **Wallet Synchronization**: Keep wallet data up-to-date with blockchain information.
3. **Collection Handling**: Manage and process collections of ordinals.
4. **SMS Functionality**: Send, receive, encrypt, and decrypt SMS messages using blockchain.
5. **Content Serving**: Serve ordinal content through a Flask server.
6. **Cross-chain Support**: Added capabilities for Bellscoin alongside Dogecoin.
7. **API Endpoints**: Comprehensive API for interacting with various functionalities.
8. **Key Management**: Generate and manage HD wallet keys, public keys, and private keys.
9. **Encryption and Decryption**: Utilities for securing sensitive data.
10. **Transaction Handling**: Send and process blockchain transactions.

# Dogecoin Arcade API

The Dogecoin Arcade API provides endpoints for managing and interacting with Dogecoin ordinals, wallet content, and SMS data.

## API Endpoints

### 1. Process Ordinal

- **URL:** `/api/process_ordinal`
- **Method:** POST
- **Description:** Initiates the processing of a Dogecoin ordinal.
- **Request Body:**
  ```json
  {
    "genesis_txid": "string",
    "depth": integer (optional, default: 1000)
  }
  ```
- **Responses:**
  - 202: Processing started
  - 400: Invalid genesis_txid
  - 503: Server busy

### 2. Process Wallet

- **URL:** `/api/process_wallet`
- **Method:** POST
- **Description:** Processes wallet files to extract ordinal information.
- **Responses:**
  - 200: Wallet processing completed
  - 500: Error during processing

### 3. Get Collection

- **URL:** `/api/getCollection`
- **Method:** POST
- **Description:** Retrieves and processes a collection of ordinals from a specified JSON file.
- **Request Body:**
  ```json
  {
    "json_file_name": "string"
  }
  ```
- **Responses:**
  - 200: Collection processing completed
  - 400: Invalid json_file_name
  - 500: Error during processing

### 4. Process SMS

- **URL:** `/api/process_sms`
- **Method:** POST
- **Description:** Processes SMS content associated with a Dogecoin ordinal.
- **Request Body:**
  ```json
  {
    "genesis_txid": "string",
    "depth": integer (optional, default: 1000)
  }
  ```
- **Responses:**
  - 200: SMS processing completed
  - 400: Invalid genesis_txid
  - 500: Error during processing

### 5. Decrypt SMS

- **URL:** `/api/decrypt_sms`
- **Method:** POST
- **Description:** Decrypts processed SMS content.
- **Responses:**
  - 200: SMS decryption completed
  - 500: Error during decryption

### 6. Get Wallet UTXOs

- **URL:** `/api/wallet/<address>`
- **Method:** GET
- **Description:** Retrieves the UTXOs for a specific wallet address.
- **Responses:**
  - 200: UTXOs retrieved successfully
  - 404: Wallet file not found
  - 500: Error reading wallet file

### 7. Get All Wallets

- **URL:** `/api/wallets`
- **Method:** GET
- **Description:** Retrieves a list of all wallet files.
- **Responses:**
  - 200: Wallet list retrieved successfully
  - 500: Error reading wallet directory

### 8. Get Address Book

- **URL:** `/api/address_book`
- **Method:** GET
- **Description:** Retrieves the address book.
- **Responses:**
  - 200: Address book retrieved successfully
  - 404: Address book file not found
  - 500: Error reading address book file

### 9. Get Ordinal Content

- **URL:** `/api/getOrdContent`
- **Method:** POST
- **Description:** Processes wallet files to extract ordinal content.
- **Responses:**
  - 200: Wallet processing completed
  - 500: Error during processing

### 10. Wallet Sync

- **URL:** `/api/walletSync`
- **Method:** POST
- **Description:** Synchronizes wallet data.
- **Responses:**
  - 200: Wallet synchronization completed successfully
  - 500: Error during wallet synchronization

### 11. Get Wallet Ordinal Content

- **URL:** `/api/getWalletOrdContent`
- **Method:** POST
- **Description:** Retrieves ordinal content from wallet files.
- **Responses:**
  - 200: Wallet ordinal content processing completed successfully
  - 500: Error during wallet ordinal content processing

### 12. Get Wallet SMS Content

- **URL:** `/api/getWalletSmsContent`
- **Method:** POST
- **Description:** Retrieves SMS content from wallet files.
- **Responses:**
  - 200: Wallet SMS content processing completed successfully
  - 500: Error during wallet SMS content processing

## Content Serving

- **URL:** `/content/<file_id>i0`
- **Method:** GET
- **Description:** Serves the content of a specific ordinal.
- **Responses:**
  - 200: Content served successfully
  - 404: Content not found
  - 503: Server busy processing ordinal

## Error Handling

- All API endpoints return JSON responses.
- HTTP status codes are used to indicate the success or failure of an API request.
- Detailed error messages are provided in the response body when applicable.

## Notes

- The API uses a global processing flag to prevent concurrent processing of ordinals.
- Some operations are handled asynchronously using a thread pool.
- Make sure to handle potential 503 (Service Unavailable) responses, as the server may be busy processing other requests.
- The content serving route (`/content/<file_id>i0`) is designed to work with HTML `src` attributes and may return various content types (HTML, images, etc.) based on the stored ordinal data.

## Setup and Usage

[Add instructions on how to set up and use the project]

## Dependencies

- Flask
- Python 3.x
- [List other major dependencies]

## Contributing

[Add information about how to contribute to the project]

## License

This project is licensed under [specify the license]. See the LICENSE file for details.

## Community

Join our Discord server for discussions and support: https://discord.gg/znM2s4VF
