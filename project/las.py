from flask import Flask, render_template, request, jsonify
import requests
import json
import warnings

# Suppress SSL verification warning
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

app = Flask(__name__)

# Configuration for LND
LND_ENDPOINT = "https://127.0.0.1:8091"  # Replace with your LND REST API endpoint for Lightning
LND_MACAROON_PATH = r"C:\Users\HomePC\.polar\networks\3\volumes\lnd\erin\data\chain\bitcoin\regtest\admin.macaroon"  # Path to your macaroon
LND_CERT_PATH = r"C:\Users\HomePC\.polar\networks\3\volumes\lnd\erin\tls.cert"  # Path to your TLS certificate

# Helper function for making Lightning RPC calls to LND
def create_lightning_invoice(amount_satoshis, date="No Date Provided", amenity="General"):
    memo = f"{amenity} Invoice due on {date}"
    payload = {
        "value": amount_satoshis,  # Amount in satoshis
        "memo": memo  # Using the date and amenity in the memo field
    }

    try:
        response = requests.post(
            f"{LND_ENDPOINT}/v1/invoices",
            headers={'Grpc-Metadata-macaroon': open(LND_MACAROON_PATH, 'rb').read().hex()},
            json=payload,
            verify=False  # Disable SSL verification for local testing
        )
        if response.status_code == 200:
            invoice = response.json()
            return invoice['payment_request']
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error creating Lightning invoice: {e}")
        return None

# Home route to show the form
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Route to handle invoice creation
@app.route('/create_invoice', methods=['POST'])
def create_invoice():
    try:
        amount = int(request.form['amount'])
        date = request.form['date']  # Extracting the date from the form
        amenity = request.form['amenity']  # Extracting the selected amenity from the form

        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero."}), 400

        # Create the invoice using the Lightning Network
        invoice = create_lightning_invoice(amount, date, amenity)
        if invoice:
            return jsonify({"payment_request": invoice}), 200
        else:
            return jsonify({"error": "Failed to create invoice."}), 500
    except ValueError:
        return jsonify({"error": "Invalid amount. Please enter a number."}), 400

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
