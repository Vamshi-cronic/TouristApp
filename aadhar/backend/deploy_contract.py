import json, os
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

print("Starting contract deployment...")

load_dotenv(dotenv_path='../../.env') 
install_solc("0.8.0")

# Load contract
try:
    with open("../contracts/kyc_registry.sol", "r") as f:
        contract_source = f.read()
except FileNotFoundError:
    print("ERROR: Could not find contract source file at ../contracts/kyc_registry.sol")
    print("Please ensure you are running this script from the 'aadhar/backend' directory.")
    exit()

print("Compiling contract...")
compiled_sol = compile_standard({
    "language": "Solidity",
    "sources": {"kyc_registry.sol": {"content": contract_source}},
    "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}}},
    solc_version="0.8.0"
)

with open("compiled.json", "w") as f:
    json.dump(compiled_sol, f)

abi = compiled_sol["contracts"]["kyc_registry.sol"]["KYCRegistry"]["abi"]
bytecode = compiled_sol["contracts"]["kyc_registry.sol"]["KYCRegistry"]["evm"]["bytecode"]["object"]

# Connect to blockchain
print("Connecting to Ganache...")
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
if not w3.is_connected():
    print("ERROR: Could not connect to Ganache at http://127.0.0.1:8545.")
    print("Please ensure Ganache is running.")
    exit()

# Read private key from .env
private_key = os.getenv("PRIVATE_KEY")
if not private_key:
    print("ERROR: PRIVATE_KEY not found in .env file.")
    exit()
    
if private_key.startswith("0x"):
    private_key = private_key[2:]
private_key = private_key.strip()

try:
    acct = w3.eth.account.from_key(private_key)
except Exception as e:
    print(f"ERROR: Invalid private key. Details: {e}")
    exit()


# Deploy
print(f"Deploying contract from account: {acct.address}...")
KYCRegistry = w3.eth.contract(abi=abi, bytecode=bytecode)

# --- FIX: Add gas and gasPrice for compatibility with ganache-cli ---
tx = KYCRegistry.constructor().build_transaction({
    "from": acct.address,
    "nonce": w3.eth.get_transaction_count(acct.address),
    "gas": 2000000,
    "gasPrice": w3.to_wei("20", "gwei")
})
# --- END FIX ---

signed_tx = acct.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"✅ Contract deployed at: {receipt.contractAddress}")

# Save ABI and address for the frontend/main app
with open("KYCRegistry.json", "w") as f:
    json.dump({"abi": abi, "address": receipt.contractAddress}, f)

print("✅ Deployment artifacts saved to KYCRegistry.json")
