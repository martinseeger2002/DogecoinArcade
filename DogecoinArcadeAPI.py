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

@app.route('/api/process_collection', methods=['POST'])
def process_collection_api():
    data = request.json
    inscription_id = data.get('inscription_id')

    if not inscription_id:
        return jsonify({"error": "Invalid inscription_id"}), 400

    try:
        process_collection(inscription_id)
        return jsonify({"message": "Collection processing completed"}), 200
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

@app.route('/favicon.ico')
def favicon():
    return send_file('favicon.ico', mimetype='image/x-icon')

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

if __name__ == '__main__':
    app.run(debug=True)