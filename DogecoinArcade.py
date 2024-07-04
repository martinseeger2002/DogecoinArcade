from flask import Flask, abort, render_template_string, send_file, request, url_for
import os
from getOrd import process_tx

app = Flask(__name__)

# HTML content for the landing page
landing_page_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dogecoin Arcade</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: url('{{ url_for('static', filename='splash.webp') }}') no-repeat center center fixed;
            background-size: cover;
            font-family: Arial, sans-serif;
            color: #fff;
            text-align: center;
            position: relative;
        }
        .container {
            background: rgba(0, 0, 0, 0.5);
            padding: 20px;
            border-radius: 10px;
        }
        h1 {
            font-size: 3em;
            margin-bottom: 20px;
        }
        input[type="text"] {
            padding: 10px;
            font-size: 1.2em;
            border: none;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        button {
            padding: 10px 20px;
            font-size: 1.2em;
            border: none;
            border-radius: 5px;
            background-color: #f90;
            color: #fff;
            cursor: pointer;
        }
        button:hover {
            background-color: #e80;
        }
        .footer {
            position: absolute;
            bottom: 10px;
            left: 10px;
            font-size: 1em;
            background: #fff;
            color: #000;
            padding: 10px;
            border-radius: 10px;
        }
        .footer a {
            color: #f90;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to Dogecoin Arcade</h1>
        <h2>The Gateway to Web Three</h2>
        <input type="text" id="inscriptionID" placeholder="Enter Inscription ID">
        <br>
        <button onclick="submitInscriptionID()">Submit</button>
    </div>
    <div class="footer">
        Created by <a href="https://x.com/MartinSeeger2" target="_blank">Martin Seeger</a> | Donations for development to DCHxodkzaKCLjmnG4LP8uH6NKynmntmCNz
    </div>

    <script>
        function submitInscriptionID() {
            var inscriptionID = document.getElementById('inscriptionID').value;
            if (inscriptionID) {
                if (inscriptionID.endsWith('i0')) {
                    window.location.href = '/content/' + encodeURIComponent(inscriptionID);
                } else {
                    window.location.href = '/content/' + encodeURIComponent(inscriptionID) + 'i0';
                }
            } else {
                alert('Please enter an inscription ID');
            }
        }

        document.addEventListener("DOMContentLoaded", function() {
            const connect2Button = document.getElementById("connect2_wallet");
            const buyButton = document.getElementById("buy");
            connect2Button.onclick = connect2;
            buyButton.onclick = buy;

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("visible");
                    } else {
                        entry.target.classList.remove("visible");
                    }
                });
            }, { threshold: 0.05 });

            document.querySelectorAll('.hidden').forEach(el => {
                observer.observe(el);
            });
        });

        async function connect2() {
            const dogeLabs = window?.dogeLabs;
            const { status } = await dogeLabs.status();
            if (status === "connected") {
                const [account] = await dogeLabs.getAccounts();
                connect2Button.innerHTML = "Connected";
                connect2Button.disabled = true;
                stak.innerHTML = account.substr(0, 7) + "..." + account.substr(-7);
                stak.disabled = true;
                fetch("/api/balance/" + account)
                    .then(response => response.json())
                    .then(data => {
                        const balance = parseFloat(data.balance) / 1e8;
                        document.getElementById("doge-balance").innerHTML = "Balance: " + balance.toFixed(3) + " DOGE";
                    })
                    .catch(error => {
                        console.error("Error:", error);
                    });
            }
        }

        async function buy() {
            if (stak.innerText === "Connect Wallet") {
                alert("Connect Wallet at the top of the page");
            } else {
                const dogeLabs = window?.dogeLabs;
                const amount = document.getElementById("mint-count").value;
                if (connect2Button.innerHTML.includes("Connected")) {
                    const transaction = await dogeLabs.sendBitcoin(MintAddress, amount * 1e8);
                    if (transaction) openModal(transaction);
                }
            }
        }

        var modal = document.getElementById("customModal");
        var btn = document.getElementById("shareButton");
        var span = document.getElementsByClassName("custom-modal-close")[0];
        var transactionLink = document.getElementById("transactionLink");

        function openModal(transactionId) {
            modal.style.display = "block";
            transactionLink.href = "https://www.oklink.com/doge/tx/" + transactionId;
            transactionLink.innerHTML = "Click to check - " + transactionId;
        }

        span.onclick = function() {
            modal.style.display = "none";
        }

        btn.onclick = function() {
            window.open('https://twitter.com/intent/tweet?text=%F0%9F%9F%A6I%20just%20minted%20RoboAI%20OG%20Pass%20from%20@RoboAI_DRC420!%0AMint%20now!%20%F0%9F%91%87%0Ahttps%3A%2F%2Fdrc-420.io%0A%23DOGINALS%20%23DRC20%20%23INSCRIPTION%20%23DRC420%20%23INSCRIPTION', '_blank');
        }

        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }

        function updateCount(amount) {
            const countInput = document.getElementById("mint-count");
            let count = parseInt(countInput.value);
            count += amount;
            if (count < 1) count = 1;
            if (count > 50) count = 50;
            countInput.value = count;
        }

        document.addEventListener("DOMContentLoaded", function() {
            fetch("/api/progress")
                .then(response => response.json())
                .then(data => {
                    document.querySelector(".progress-fill").style.width = data.progress + "%";
                    document.getElementById("progress-percent").innerHTML = data.progress + "% Minted";
                    document.getElementById("mint-count").innerHTML = data.minted + " / " + data.total;
                });
        });

        var countDownDate = new Date("Apr 9, 2024 15:00:00 UTC").getTime();
        var x = setInterval(function() {
            var now = new Date().getTime();
            var distance = countDownDate - now;

            var days = Math.floor(distance / (1000 * 60 * 60 * 24));
            var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            var seconds = Math.floor((distance % (1000 * 60)) / 1000);

            document.getElementById("timer").innerHTML = days + "d " + hours + "h " + minutes + "m " + seconds + "s ";

            if (distance < 0) {
                clearInterval(x);
                document.getElementById("timer").innerHTML = "MINT LIVE";
                buyButton.disabled = false;
            }
        }, 1000);

        function openPopup(popup) {
            $(popup).fadeIn().css("display", "flex");
            $(popup).next().siblings(".hidden").fadeOut();
            $("body").css("overflow", "hidden");
        }

        function closePopup() {
            $(".customModal").fadeOut();
            $("body").css("overflow", "auto");
        }
    </script>
</body>
</html>
'''

@app.route('/')
def landing_page():
    return render_template_string(landing_page_html)

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
        elif file_extension == '.webp':
            return send_file(file_path, mimetype='image/webp')  # Display .webp file in the browser
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
        try:
            process_tx(genesis_txid, depth=500)
        except JSONRPCException as e:
            print(f"JSONRPCException: {e}")
            return "Error processing transaction", 500
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
        <p>Extracting Ord, check terminal and click refresh when num_chunk=0...</p>
    </body>
    </html>
    '''
    return render_template_string(html_content), 404

if __name__ == '__main__':
    app.run()
