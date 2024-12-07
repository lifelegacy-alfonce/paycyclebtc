import requests
import json
import warnings

# Suppress SSL verification warning
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

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

    cert = open(LND_CERT_PATH, 'rb').read()
    payload = json.dumps({"jsonrpc": "1.0", "id": "python-script", "method": method, "params": params})

    try:
        response = requests.post(
            f"{LND_ENDPOINT}/{method}",
            headers=headers,
            data=payload,
            cert=(LND_CERT_PATH, cert),
            verify=False  # Disable SSL verification for local testing
        )
        response.raise_for_status()
        return response.json().get("result")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to LND node: {e}")
        return None

# Example Bitcoin operation: Creating a new address and mining a block
def create_bitcoin_address_and_mine():
    new_address = rpc_call("getnewaddress")
    if new_address:
        print(f"New Bitcoin Address: {new_address}")

        # Mine a block to the new address (for regtest mode)
        mined_block = rpc_call("generatetoaddress", [1, new_address])
        if mined_block:
            print(f"Mined Block Hash: {mined_block}")

# Example Lightning operation: Creating a Lightning invoice
def create_lightning_invoice(amount_satoshis, memo="Test Invoice"):
    payload = {
        "value": amount_satoshis,  # Amount in satoshis
        "memo": memo               # Optional memo for the invoice
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
            print(f"Invoice created successfully! Payment Request: {invoice['payment_request']}")
            return invoice['payment_request']
        else:
            print(f"Failed to create invoice: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error creating Lightning invoice: {e}")
        return None

def main():
    # Create Bitcoin address and mine a block (for testing)
    create_bitcoin_address_and_mine()

    # Create Lightning invoice for 1000 satoshis
    lightning_invoice = create_lightning_invoice(1000, "Test Lightning Invoice")
    if lightning_invoice:
        print(f"Created Lightning invoice: {lightning_invoice}")
    else:
        print("Failed to create Lightning invoice")

if __name__ == "__main__":
    main()
