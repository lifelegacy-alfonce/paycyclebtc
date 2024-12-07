from flask import Flask, render_template, request, jsonify
import requests
import json

app = Flask(__name__)

# Configuration
POLAR_ENDPOINT = "http://127.0.0.1:18444"  # Replace with your Polar node endpoint for Bitcoin
LND_ENDPOINT = "https://127.0.0.1:8091"  # Replace with your LND REST API endpoint for Lightning
RPC_USER = "polaruser"  # Replace with your Polar RPC username
RPC_PASSWORD = "polarpass"  # Replace with your Polar RPC password
LND_MACAROON_PATH = r"C:\Users\HomePC\.polar\networks\3\volumes\lnd\erin\data\chain\bitcoin\regtest\admin.macaroon"  # Path to your macaroon
LND_CERT_PATH = r"C:\Users\HomePC\.polar\networks\3\volumes\lnd\erin\tls.cert"  # Path to your TLS certificate

# Helper function for making Bitcoin RPC calls
def rpc_call(method, params=None):
    if params is None:
        params = []
    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({"jsonrpc": "1.0", "id": "python-script", "method": method, "params": params})
    try:
        response = requests.post(
            POLAR_ENDPOINT,
            headers=headers,
            data=payload,
            auth=(RPC_USER, RPC_PASSWORD)
        )
        response.raise_for_status()  # Raise an error for HTTP errors
        return response.json().get("result")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Polar node: {e}")
        return None

# Helper function for making Lightning RPC calls to LND
def lnd_rpc_call(method, params=None):
    if params is None:
        params = []
    headers = {
        'Grpc-Metadata-macaroon': open(LND_MACAROON_PATH, 'rb').read().hex(),
        'Content-Type': 'application/json'
    }

    # Ensure correct handling of the certificate
    with open(LND_CERT_PATH, 'rb') as cert_file:
        cert = cert_file.read()

    payload = json.dumps({"jsonrpc": "1.0", "id": "python-script", "method": method, "params": params})

    try:
        response = requests.post(
            f"{LND_ENDPOINT}/{method}",
            headers=headers,
            data=payload,
            cert=(LND_CERT_PATH, cert),  # Use the certificate
            verify=False  # Disable SSL verification for local testing
        )
        response.raise_for_status()
        return response.json().get("result")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to LND node: {e}")
        return None

# Route to display the form for invoice creation
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle the invoice creation request
@app.route('/create_invoice', methods=['POST'])
def create_invoice():
    try:
        # Extracting data from the form
        amount = int(request.form['amount'])  # Amount in satoshis
        date = request.form['date']  # Rent due date (if needed)

        # Create the Lightning invoice
        payment_request = lnd_rpc_call('v1/invoices', {"value": amount, "memo": f"Invoice for rent due {date}"})
        
        if payment_request:
            return render_template('invoice.html', payment_request=payment_request)
        else:
            return jsonify({"error": "Failed to create invoice"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
