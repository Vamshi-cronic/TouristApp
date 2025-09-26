import json, uuid, os, random, qrcode
from web3 import Web3
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from eth_hash.auto import keccak
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# --- Blockchain setup ---
with open("KYCRegistry.json") as f:
    contract_data = json.load(f)

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
acct = w3.eth.account.from_key(os.getenv("PRIVATE_KEY"))
contract = w3.eth.contract(
    address=contract_data["address"],
    abi=contract_data["abi"]
)

# --- Twilio setup ---
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

# --- Dummy users (like Aadhaar database) ---
dummy_users = {
    "123456789012": {
        "aadhaar": "123456789012",
        "name": "Ravi Kumar",
        "dob": "1990-01-01",
        "address": "New Delhi, India",
        "mobile": "+919182378228",
        "email": "ravi.kumar@example.com"
    },
    "987654321098": {
        "aadhaar": "987654321098",
        "name": "Anita Sharma",
        "dob": "1992-05-14",
        "address": "Mumbai, India",
        "mobile": "+919182378228",
        "email": "anita.sharma@example.com"
    }
}

# --- OTP store ---
otps = {}

# --- AES key ---
SECRET_KEY = get_random_bytes(16)

# ---------------- OTP ----------------
def send_otp(user):
    otp = str(random.randint(100000, 999999))
    otps[user["aadhaar"]] = otp
    twilio_client.messages.create(
        body=f"Your Aadhaar KYC OTP is {otp}",
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=user["mobile"]
    )
    print("✅ OTP sent to registered mobile")

def verify_otp(aadhaar, otp):
    return otps.get(aadhaar) == otp

# ---------------- Encryption ----------------
def encrypt_payload(payload):
    cipher = AES.new(SECRET_KEY, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(json.dumps(payload).encode())
    return {"ciphertext": ciphertext.hex(), "nonce": cipher.nonce.hex(), "tag": tag.hex()}

def decrypt_payload(data):
    cipher = AES.new(SECRET_KEY, AES.MODE_EAX, nonce=bytes.fromhex(data["nonce"]))
    decrypted = cipher.decrypt_and_verify(bytes.fromhex(data["ciphertext"]), bytes.fromhex(data["tag"]))
    return json.loads(decrypted.decode())

# ---------------- KYC Register ----------------
def register_kyc(user):
    kyc_id = "KYC_" + str(uuid.uuid4())[:8]  # generate dynamic KYC ID
    user["kyc_id"] = kyc_id

    encrypted = encrypt_payload(user)

    # Save locally
    try:
        with open("storage.json", "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    except FileNotFoundError:
        data = {}

    data[kyc_id] = encrypted
    with open("storage.json", "w") as f:
        json.dump(data, f, indent=4)

    # Hash payload
    payload_str = json.dumps(user, sort_keys=True)
    kyc_hash = keccak(payload_str.encode('utf-8'))


    # Store hash on blockchain
    tx = contract.functions.registerKYC(kyc_id, kyc_hash).build_transaction({
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": 2000000,
        "gasPrice": w3.to_wei("50", "gwei")
    })
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)

    # Generate QR with KYC ID
    qr = qrcode.make(kyc_id)
    qr.save(f"{kyc_id}.png")

    print(f"✅ KYC registered!\nKYC ID: {kyc_id}\nQR Code: {kyc_id}.png")
    return kyc_id

# ---------------- KYC Retrieve ----------------
def get_kyc(kyc_id):
    try:
        with open("storage.json") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print("❌ Storage file is empty or corrupted")
                return
    except FileNotFoundError:
        print("❌ No KYC records found")
        return

    encrypted = data.get(kyc_id)
    if not encrypted:
        print("❌ KYC not found")
        return

    user = decrypt_payload(encrypted)
    recomputed = keccak(json.dumps(user, sort_keys=True).encode('utf-8')).hex()


    record = contract.functions.getKYC(kyc_id).call()
    valid = recomputed == record[1].hex()

    print("✅ Verified on blockchain:", valid)
    print("📄 User details:", user)

# ---------------- Console Flow ----------------
if __name__ == "__main__":
    aadhaar = input("Enter Aadhaar: ")
    if aadhaar not in dummy_users:
        print("❌ User not found")
        exit()

    user = dummy_users[aadhaar]
    send_otp(user)
    otp = input("Enter OTP: ")
    if verify_otp(aadhaar, otp):
        kyc_id = register_kyc(user)
        print("🔑 Save this KYC ID (also in QR):", kyc_id)
    else:
        print("❌ Invalid OTP")
        exit()

    # Fetch KYC by entering ID from scanned QR (Google Lens)
    kid = input("Enter KYC ID from scanned QR: ")
    get_kyc(kid)
