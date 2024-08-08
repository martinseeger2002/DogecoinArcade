
# Dogecoin Arcade Project

This project involves a comprehensive system for managing and interacting with Dogecoin ordinals, including tools for collection management, content handling, and blockchain interaction. Below is a detailed overview of the project structure and components.

## Project Structure

### collections

The `collections` folder contains several JSON files that define various collections. Each collection has metadata and items associated with it.

---

### content

The `content` folder contains all the ordinal content files. These files can be of any type, and their names correspond to their genesis ordinal transaction IDs.

---

### indexes

The `indexes` folder contains an index text file for each ordinal. The name of each text file corresponds to the genesis transaction ID. Each text file contains the subsequent transaction IDs for ordinals that required more than one transaction.

---

### jsonTools

The `jsonTools` folder contains a program that processes a `DM.json` file and outputs a Dogecoin Arcade collection JSON.

---

### simple_scripts

The `simple_scripts` folder contains a collection of tools used to view transaction data and interact with the blockchain in different ways.

---

### static

The `static` folder contains non-doginal content files.

---

### templates

The `templates` folder contains non-doginal HTML files and JavaScript code for Dogecoin Arcade.

---

### CallGetCollection.py

This script calls `getCollection` with the defined collection JSON and retrieves all the ordinal data from the blockchain. It saves this data to files in the `content` folder by calling `getOrd`.

---

### CallSendOrd.py

This script sends an ordinal using `sendOrd` with the defined receiving wallet, the transaction ID (txid), and the index.

---

### DogecoinArcade.py

This script is a Flask server that serves the content of the ordinals. It either retrieves the content from the `content` folder or calls `getOrd` and then displays it from the `content` folder.

---

### callGetOrd.py

This script calls `getOrd` to retrieve data for a specific ordinal and saves it to the appropriate file.

---

### eraseContent.py

This script deletes all content below a specified size threshold.

---

### eraseIndexes.py

This script deletes all index files below a specified size threshold.

---

### favicon.ico

This file is the favicon for the Dogecoin Arcade website, displayed in the browser tab.

---

### getCollection.py

This script retrieves the ordinal data for each transaction ID in the collection JSON.

---

### getOrdContent.py

This program extracts the ordinal content data and saves it in the `content` folder. It also creates or updates the index files in the `indexes` folder for the defined transaction ID (txid).

---

### getWalletOrdContent.py

This script retrieves all the ordinals from the genesis transaction ID (txid) in the wallet's JSON.

---

### rpc.conf

This file contains the RPC credentials.

---

### sendOrd.py

This script sends an ordinal using one transaction ID and index defining the ordinal and another transaction ID in the sending wallet that is "not an ord."

---

### walletSync.py

This script creates and updates JSON files in the `wallets` directory. Each wallet file is named after the wallet's receiving address.

Example of a wallet JSON file:

```json
[
    {
        "txid": "c8b94184b7e873572d68a2c8b5377d10c531851a69d97720be43a4d3536e3803",
        "vout": 0,
        "amount": 0.001,
        "genesis_txid": null
    },
    {
        "txid": "4e11b4526d16dc933ac5aff2df23e6ad7cfd5b0c0f9717ae7aed5dbe7e189203",
        "vout": 1,
        "amount": 2.58826836,
        "genesis_txid": "not an ord"
    },
    {
        "txid": "113aed7a4e898e83fa28a245b9a1e6651f71f275d98ca6fb4e077b2497017b90",
        "vout": 0,
        "amount": 0.001,
        "genesis_txid": "c51e48d09f8a7f221a16a6d2f64899471eb83b1879ec64bc26e6fc1cd19ed722"
    }
]
```
How to send a sms
```
node . sms DC2f4XCWsJ7iZTNLH41S9NsTqH4zqJ19Es text.txt
