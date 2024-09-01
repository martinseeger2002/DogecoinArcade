import os
from flask import Flask, render_template, jsonify, abort, request, redirect, url_for
import requests
from jinja2.exceptions import TemplateNotFound
import math

app = Flask(__name__)

API_BASE_URL = os.environ.get('API_BASE_URL', 'http://192.168.68.73:5000')
WEBSITE_PORT = int(os.environ.get('WEBSITE_PORT', 5001))
UTXOS_PER_PAGE = 10

print(f"API_BASE_URL is set to: {API_BASE_URL}")

@app.route('/')
def home():
    try:
        return render_template('home.html', api_base_url=API_BASE_URL)
    except TemplateNotFound:
        abort(500, description="Template not found")

@app.route('/wallets')
def wallets():
    try:
        response = requests.get(f"{API_BASE_URL}/api/wallets")
        if response.status_code == 200:
            wallet_data = response.json()['wallets']
            return render_template('wallets.html', wallets=wallet_data, api_base_url=API_BASE_URL)
        else:
            abort(500, description="Failed to fetch wallet data")
    except requests.RequestException as e:
        abort(500, description=f"Error connecting to API: {str(e)}")
    except TemplateNotFound:
        abort(500, description="Template not found")

@app.route('/wallet/<address>')
def wallet_details(address):
    try:
        page = request.args.get('page', 1, type=int)
        response = requests.get(f"{API_BASE_URL}/api/wallet/{address}")
        if response.status_code == 200:
            wallet_data = response.json()
            utxos = wallet_data['utxos']
            total_utxos = len(utxos)
            total_pages = math.ceil(total_utxos / UTXOS_PER_PAGE)
            start_index = (page - 1) * UTXOS_PER_PAGE
            end_index = start_index + UTXOS_PER_PAGE
            paginated_utxos = utxos[start_index:end_index]
            ord_count = sum(1 for utxo in utxos if utxo['genesis_txid'] != "not an ord")
            non_ord_amount = sum(utxo['amount'] for utxo in utxos if utxo['genesis_txid'] == "not an ord")
            print(f"Rendering template with api_base_url: {API_BASE_URL}")
            return render_template('wallet_details.html', 
                                   address=address, 
                                   utxos=paginated_utxos, 
                                   page=page, 
                                   total_pages=total_pages,
                                   ord_count=ord_count,
                                   non_ord_amount=non_ord_amount,
                                   api_base_url=API_BASE_URL)
        else:
            abort(500, description="Failed to fetch wallet details")
    except requests.RequestException as e:
        abort(500, description=f"Error connecting to API: {str(e)}")
    except TemplateNotFound:
        abort(500, description="Template not found")

@app.route('/wallet_sync', methods=['POST'])
def wallet_sync():
    try:
        response = requests.post(f"{API_BASE_URL}/api/walletSync")
        if response.status_code == 200:
            return redirect(url_for('wallets'))
        else:
            abort(500, description="Failed to sync wallets")
    except requests.RequestException as e:
        abort(500, description=f"Error connecting to API: {str(e)}")

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', message=str(e.description), api_base_url=API_BASE_URL), 500

if __name__ == '__main__':
    print(f"Website server running on http://0.0.0.0:{WEBSITE_PORT}")
    print(f"API server expected at {API_BASE_URL}")
    app.run(host='0.0.0.0', port=WEBSITE_PORT, debug=True)