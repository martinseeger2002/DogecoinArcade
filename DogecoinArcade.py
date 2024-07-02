from flask import Flask, abort, render_template_string, send_file, request
import os
from getOrd import process_tx

app = Flask(__name__)

@app.route('/content/<file_id>i0')
def serve_content(file_id):
    filename = f"{file_id}"
    content_dir = './content'
    file_path = None
    file_extension = None

    # Look for a file with the matching base name
    for file in os.listdir(content_dir):
        if file.startswith(filename):
            file_path = os.path.join(content_dir, file)
            file_extension = os.path.splitext(file)[1]
            break

    if file_path and os.path.isfile(file_path):
        print(f"File found: {file_path}")  # Debug log

        if file_extension == '.html':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return render_template_string(html_content)
            except Exception as e:
                print(f"Error reading HTML file: {e}")
                abort(500)
        else:
            return send_file(file_path)  # For other file types, send the file directly
    else:
        print(f"File not found: {filename} in {content_dir}")  # Debug log
        print(f"Current working directory: {os.getcwd()}")  # Print current working directory
        print(f"Content directory contents: {os.listdir(content_dir)}")  # List content directory contents
        abort(404)

@app.errorhandler(404)
def not_found_error(error):
    # Extract the genesis_txid from the request path
    request_path = request.path.split('/')[-1]
    if request_path.endswith('i0'):
        genesis_txid = request_path[:-2]  # Remove the trailing 'i0'
    else:
        genesis_txid = request_path

    if genesis_txid != 'favicon.ico':
        print(f"404 Error: Processing transaction for genesis_txid: {genesis_txid}")
        process_tx(genesis_txid, depth=500)
    else:
        print("404 Error: favicon.ico requested, not processing transaction.")
    
    # HTML content with JavaScript to wait and refresh the page
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Content Not Found</title>
        <meta http-equiv="refresh" content="5">
    </head>
    <body>
        <p>Content not found. The page will refresh shortly...</p>
    </body>
    </html>
    '''
    return render_template_string(html_content), 404

if __name__ == '__main__':
    app.run(debug=True)
