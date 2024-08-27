from flask import Flask, abort, render_template, render_template_string, send_file, request, jsonify
import os
from threading import Lock, local
from concurrent.futures import ThreadPoolExecutor
import re
import queue
from getOrdContent import process_tx
from bitcoinrpc.authproxy import JSONRPCException
from getWalletOrdContent import process_wallet_files
from getCollection import process_inscription_id as process_collection
from getSmsContent import process_tx as process_sms
from decryptWalletSmsContent import main as decrypt_sms
from sendOrd import send_ord
import logging
import json
from flask import url_for
import subprocess  # Add this line

app = Flask(__name__)

# Queue to manage tasks
task_queue = queue.Queue()
# Thread pool to handle concurrent processing
thread_pool = ThreadPoolExecutor(max_workers=4)
# Thread-local storage for RPC connections
thread_local = local()

# Shared flag and lock to indicate processing state
processing_flag = False
processing_lock = Lock()

def get_rpc_connection():
    if not hasattr(thread_local, "rpc_connection"):
        from getOrdContent import rpc_connection
        thread_local.rpc_connection = rpc_connection
    return thread_local.rpc_connection

def is_hexadecimal(s):
    """Check if the string s is a valid hexadecimal string."""
    return re.fullmatch(r'^[0-9a-fA-F]+$', s) is not None

def process_task(genesis_txid, depth=1000):
    global processing_flag
    with processing_lock:
        processing_flag = True
    try:
        print(f"Starting processing for {genesis_txid}")
        process_tx(genesis_txid, depth)
    except JSONRPCException as e:
        print(f"JSONRPCException: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        with processing_lock:
            processing_flag = False
        print(f"Finished processing for {genesis_txid}")
        task_queue.task_done()

@app.route('/')
def landing_page():
    return render_template('landing_page.html')

@app.route('/content/<file_id>i0')
def serve_content(file_id):
    global processing_flag
    with processing_lock:
        if processing_flag:
            return "Server is busy processing ordinal. Please try again later.", 503

    filename = f"{file_id}"
    content_dir = './content'
    file_path = next((os.path.join(content_dir, file) for file in os.listdir(content_dir) if file.startswith(filename)), None)
    
    if file_path and os.path.isfile(file_path):
        print(f"File found: {file_path}")

        if file_path.endswith('.html'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return render_template_string(html_content)
            except Exception as e:
                print(f"Error reading HTML file: {e}")
                abort(500)
        elif file_path.endswith('.webp'):
            return send_file(file_path, mimetype='image/webp')
        else:
            return send_file(file_path)
    else:
        print(f"File not found: {filename} in {content_dir}")
        abort(404)

@app.route('/api/process_ordinal', methods=['POST'])
def process_ordinal_api():
    data = request.json
    genesis_txid = data.get('genesis_txid')
    depth = data.get('depth', 1000)

    if not genesis_txid or not is_hexadecimal(genesis_txid):
        return jsonify({"error": "Invalid genesis_txid"}), 400

    with processing_lock:
        if not processing_flag:
            thread_pool.submit(process_task, genesis_txid, depth)
            return jsonify({"message": "Processing ordinal started"}), 202
        else:
            return jsonify({"message": "Server is busy processing another ordinal. Please try again later."}), 503

@app.route('/api/process_wallet', methods=['POST'])
def process_wallet_api():
    try:
        process_wallet_files()
        return jsonify({"message": "Wallet processing completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from getCollection import get_collection  # Update this import

@app.route('/api/getCollection', methods=['POST'])
def get_collection_api():
    data = request.json
    json_file_name = data.get('json_file_name')

    if not json_file_name:
        return jsonify({"error": "Invalid json_file_name"}), 400

    try:
        # Append .json to the filename
        full_json_file_name = f"{json_file_name}.json"
        result = get_collection(full_json_file_name)
        return jsonify({"message": "Collection processing completed", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/process_sms', methods=['POST'])
def process_sms_api():
    data = request.json
    genesis_txid = data.get('genesis_txid')
    depth = data.get('depth', 1000)

    if not genesis_txid or not is_hexadecimal(genesis_txid):
        return jsonify({"error": "Invalid genesis_txid"}), 400

    try:
        process_sms(genesis_txid, depth)
        return jsonify({"message": "SMS processing completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/decrypt_sms', methods=['POST'])
def decrypt_sms_api():
    try:
        decrypt_sms()
        return jsonify({"message": "SMS decryption completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/api/send_ord', methods=['POST'])
# def send_ord_api():
#     data = request.json
#     utxo_txid = data.get('utxo_txid')
#     utxo_vout = data.get('utxo_vout')
#     recipient_address = data.get('recipient_address')

#     if not all([utxo_txid, isinstance(utxo_vout, int), recipient_address]):
#         return jsonify({"error": "Invalid input. Please provide utxo_txid, utxo_vout, and recipient_address"}), 400

#     try:
#         result = send_ord(utxo_txid, utxo_vout, recipient_address)
#         return jsonify({"message": "Ordinal sent successfully", "result": result}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/<address>', methods=['GET'])
def get_wallet_utxos(address):
    wallet_dir = './wallets'
    wallet_file = f"{address}.json"
    wallet_path = os.path.join(wallet_dir, wallet_file)

    logging.info(f"Attempting to access wallet file: {wallet_path}")

    if not os.path.exists(wallet_path):
        logging.error(f"Wallet file not found: {wallet_path}")
        return jsonify({"error": "Wallet file not found"}), 404

    try:
        with open(wallet_path, 'r') as file:
            utxos = json.load(file)
        
        # The entire file content is the list of UTXOs
        logging.info(f"Successfully retrieved UTXOs for address: {address}")
        return jsonify({"address": address, "utxos": utxos}), 200
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in wallet file: {wallet_path}. Error: {str(e)}")
        return jsonify({"error": "Invalid JSON in wallet file"}), 500
    except Exception as e:
        logging.error(f"Error reading wallet file: {wallet_path}. Error: {str(e)}")
        return jsonify({"error": f"Error reading wallet file: {str(e)}"}), 500

@app.route('/api/wallets', methods=['GET'])
def get_wallet_files():
    wallet_dir = './wallets'
    try:
        files = os.listdir(wallet_dir)
        # Create relative links for each wallet file
        wallet_links = [
            f"/api/wallet/{os.path.splitext(file)[0]}"
            for file in files
        ]
        return jsonify({"wallets": wallet_links}), 200
    except Exception as e:
        return jsonify({"error": f"Error reading wallet directory: {str(e)}"}), 500

@app.errorhandler(404)
def not_found_error(error):
    global processing_flag
    request_path = request.path.split('/')[-1]
    genesis_txid = request_path[:-2] if request_path.endswith('i0') else None

    if not genesis_txid or not is_hexadecimal(genesis_txid):
        print(f"Invalid genesis_txid: {request_path}")
        return "Invalid transaction ID", 400

    with processing_lock:
        if not processing_flag:
            thread_pool.submit(process_task, genesis_txid, 1000)

    return "Processing ordinal, click refresh when complete", 404

@app.route('/api/address_book', methods=['GET'])
def get_address_book():
    address_book_path = './sms/addressBook.json'

    logging.info(f"Attempting to access address book file: {address_book_path}")

    if not os.path.exists(address_book_path):
        logging.error(f"Address book file not found: {address_book_path}")
        return jsonify({"error": "Address book file not found"}), 404

    try:
        with open(address_book_path, 'r') as file:
            address_book = json.load(file)
        
        logging.info("Successfully retrieved address book")
        return jsonify(address_book), 200
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in address book file. Error: {str(e)}")
        return jsonify({"error": "Invalid JSON in address book file"}), 500
    except Exception as e:
        logging.error(f"Error reading address book file. Error: {str(e)}")
        return jsonify({"error": f"Error reading address book file: {str(e)}"}), 500

@app.route('/api/getOrdContent', methods=['POST'])
def get_ord_content_api():
    try:
        process_wallet_files()
        return jsonify({"message": "Wallet processing completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/walletSync', methods=['POST'])
def wallet_sync_api():
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to walletSync.py
        wallet_sync_path = os.path.join(current_dir, 'walletSync.py')
        
        # Run walletSync.py as a subprocess
        result = subprocess.run(['python', wallet_sync_path], capture_output=True, text=True, check=True)
        
        # Check if the script ran successfully
        if result.returncode == 0:
            return jsonify({"message": "Wallet synchronization completed successfully"}), 200
        else:
            return jsonify({"error": f"Wallet synchronization failed: {result.stderr}"}), 500
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during wallet synchronization: {e.stderr}")
        return jsonify({"error": f"Wallet synchronization failed: {e.stderr}"}), 500
    except Exception as e:
        logging.error(f"Unexpected error during wallet synchronization: {str(e)}")
        return jsonify({"error": f"Unexpected error during wallet synchronization: {str(e)}"}), 500

@app.route('/api/getWalletOrdContent', methods=['POST'])
def get_wallet_ord_content_api():
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to getWalletOrdContent.py
        wallet_ord_content_path = os.path.join(current_dir, 'getWalletOrdContent.py')
        
        # Run getWalletOrdContent.py as a subprocess
        result = subprocess.run(['python', wallet_ord_content_path], capture_output=True, text=True, check=True)
        
        # Check if the script ran successfully
        if result.returncode == 0:
            return jsonify({"message": "Wallet ordinal content processing completed successfully", "output": result.stdout}), 200
        else:
            return jsonify({"error": f"Wallet ordinal content processing failed: {result.stderr}"}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Error during wallet ordinal content processing: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error during wallet ordinal content processing: {str(e)}"}), 500

@app.route('/api/getWalletSmsContent', methods=['POST'])
def get_wallet_sms_content_api():
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to getWalletSmsContent.py
        wallet_sms_content_path = os.path.join(current_dir, 'getWalletSmsContent.py')
        
        # Run getWalletSmsContent.py as a subprocess
        result = subprocess.run(['python', wallet_sms_content_path], capture_output=True, text=True, check=True)
        
        # Check if the script ran successfully
        if result.returncode == 0:
            return jsonify({"message": "Wallet SMS content processing completed successfully", "output": result.stdout}), 200
        else:
            return jsonify({"error": f"Wallet SMS content processing failed: {result.stderr}"}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Error during wallet SMS content processing: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error during wallet SMS content processing: {str(e)}"}), 500

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5000, debug=True)