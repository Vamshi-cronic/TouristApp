
from dotenv import load_dotenv
load_dotenv()

import os
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_apscheduler import APScheduler
import random
from datetime import datetime
import qrcode
import json
from web3 import Web3
import binascii

import database
import external_data
import anomaly_detection
from disaster_prediction import DisasterPredictionModel

# ------------------ App Setup ------------------
app = Flask(__name__, template_folder='templates')
app.secret_key = "a_very_secret_key_that_should_be_in_an_env_file"
app.config['SCHEDULER_TIMEZONE'] = 'UTC'
bcrypt = Bcrypt(app)

# --- In-memory Stores ---
external_danger_zones = []
anomaly_detectors = {}
disaster_model = DisasterPredictionModel()

# --- ADDED: Dummy User Data ---
dummy_users = {
    "123456789012": {"name": "Rahul Sharma", "dob": "1985-05-20", "mobile": "9876543210", "email": "rahul.sharma@example.com"},
    "210987654321": {"name": "Priya Patel", "dob": "1992-08-15", "mobile": "9123456789", "email": "priya.patel@example.com"},
    "345678901234": {"name": "Amit Singh", "dob": "1990-11-30", "mobile": "9988776655", "email": "amit.singh@example.com"}
}

# --- Blockchain setup: Load pre-deployed contract ---
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
contract = None

def load_contract():
    """Loads the contract from the JSON file created by the deployment script."""
    global contract
    try:
        with open("aadhar/backend/KYCRegistry.json", "r") as f:
            contract_data = json.load(f)
        contract_address = contract_data["address"]
        contract_abi = contract_data["abi"]
        
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            print("FATAL: PRIVATE_KEY is not set.")
            return
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        acct = w3.eth.account.from_key(private_key.strip())
        w3.eth.default_account = acct.address

        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        print(f"✅ Contract loaded successfully from address: {contract.address}")
        print(f"✅ Default account set to: {w3.eth.default_account}")

    except FileNotFoundError:
        print("="*70)
        print("FATAL: Contract JSON file not found!")
        print("Please run the deployment script first from the 'aadhar/backend' directory:")
        print("  source ../../.venv/bin/activate  ")
        print("  python deploy_contract.py        ")
        print("="*70)
    except Exception as e:
        print(f"FATAL: An error occurred while loading the contract: {e}")

# ------------------ Auth Routes ------------------
@app.route("/")
def main_page():
    return render_template("main_page.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin = database.get_admin(username)
        if admin and bcrypt.check_password_hash(admin['password_hash'], password):
            session["admin"] = username
            return redirect(url_for("admin_map"))
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

@app.route('/tourist_login')
def tourist_login():
    return render_template('tourist_login.html')

@app.route("/get_otp", methods=['POST'])
def get_otp():
    aadhaar = request.json.get('aadhaar')
    if not (aadhaar and len(aadhaar) == 12 and aadhaar.isdigit()):
        return jsonify({"status": "error", "message": "Invalid Aadhaar number"}), 400
    # MODIFIED: Check if user exists
    if aadhaar not in dummy_users:
        return jsonify({"status": "error", "message": "Aadhaar number not found in our records."}), 404

    otp = str(random.randint(100000, 999999))
    session['otp'] = otp
    session['aadhaar'] = aadhaar
    
    print(f"OTP for Aadhaar  {aadhaar}: {otp}")
    print(f"------------------------------------")
    return jsonify({"status": "success", "message": "OTP sent (check console).",'otp':otp})

@app.route("/verify_otp", methods=['POST'])
def verify_otp():
    aadhaar = request.json.get('aadhaar')
    otp = request.json.get('otp')
    
    if aadhaar != session.get('aadhaar') or otp != session.get('otp'):
        return jsonify({"status": "error", "message": "Invalid OTP"}), 400

    session['tourist_logged_in'] = True
    session['user_id'] = aadhaar 
    session.pop('otp', None)

    return jsonify({"status": "success"})

@app.route("/api/register_kyc_on_blockchain", methods=['POST'])
def register_kyc_on_blockchain():
    if contract is None:
        return jsonify({"status": "error", "message": "Contract not loaded. Check server logs."}), 500

    if not session.get('tourist_logged_in'):
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    aadhaar = session.get('user_id')
    if not aadhaar:
        return jsonify({"status": "error", "message": "Aadhaar number not found"}), 400

    # --- MODIFIED: Fetch user data from dummy_users ---
    user_details = dummy_users.get(aadhaar)
    if not user_details:
        return jsonify({"status": "error", "message": "User details not found for this Aadhaar number."}), 404

    user_data_for_hash = {"aadhaar": aadhaar, "name": user_details["name"], "dob": user_details["dob"]}
    kyc_id = "KYC_" + str(uuid.uuid4())[:8]
    payload_str = json.dumps(user_data_for_hash, sort_keys=True)
    kyc_hash = Web3.keccak(text=payload_str)

    try:
        tx_hash = contract.functions.registerKYC(kyc_id, kyc_hash).transact()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"KYC ID: {kyc_id} for user {user_details['name']} registered on blockchain.")

        # --- MODIFIED: Return full user details in the response ---
        response_data = {
            "status": "success",
            "kyc_id": kyc_id,
            "name": user_details["name"],
            "email": user_details["email"],
            "mobile": user_details["mobile"],
            "tx_hash": receipt.transactionHash.hex()
        }
        return jsonify(response_data)

    except Exception as e:
        print(f"ERROR during blockchain transaction: {e}")
        return jsonify({"status": "error", "message": "Blockchain registration failed."}), 500

# ------------------ Admin & Map Routes (UNCHANGED) ------------------
@app.route("/admin")
def admin_map():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    return render_template("map.html")

@app.route("/add_zone", methods=["POST"])
def add_zone():
    if "admin" not in session: return jsonify({"status": "error", "message": "Unauthorized"}), 401
    data = request.json
    if data and all(k in data for k in ["lat", "lng", "radius", "description"]):
        new_id = database.add_zone(data["lat"], data["lng"], data["radius"], data["description"], data.get("type", "manual"))
        return jsonify({"status": "success", "id": new_id})
    return jsonify({"status": "error", "message": "Invalid data"}), 400

@app.route("/get_zones")
def get_zones():
    db_zones = database.get_all_zones()
    all_zones = db_zones + external_danger_zones
    return jsonify(all_zones)

@app.route("/delete_zone/<string:zone_id>", methods=["DELETE"])
def delete_zone(zone_id):
    if "admin" not in session: return jsonify({"status": "error", "message": "Unauthorized"}), 401
    if database.delete_zone_by_id(zone_id):
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Zone ID not found"}), 404

# ------------------ Tourist Routes & API (UNCHANGED) ------------------
@app.route("/tourist_route")
def tourist_route():
    if not session.get('tourist_logged_in'):
        return redirect(url_for('tourist_login'))
    
    if '_id' not in session:
        session['_id'] = str(uuid.uuid4())
    return render_template("tourist_route.html")

@app.route("/api/tourist_location", methods=["POST"])
def handle_tourist_location():
    data = request.json
    user_id = session.get('_id', request.remote_addr)
    if data and "lat" in data and "lng" in data and "timestamp" in data:
        database.add_tourist_location(user_id, data["lat"], data["lng"], data["timestamp"])
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid location data"}), 400

@app.route("/api/tourist_locations")
def get_tourist_locations():
    if "admin" not in session: return jsonify({"status": "error", "message": "Unauthorized"}), 401
    locations = database.get_latest_tourist_locations()
    return jsonify(locations)

@app.route("/api/police_locations")
def get_police_locations():
    if "admin" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    bbox = request.args.get('bbox')
    if not bbox:
        return jsonify({"status": "error", "message": "Bounding box ('bbox') is required."}), 400

    locations = external_data.fetch_police_locations_from_api(bbox)
    return jsonify(locations)

# ------------------ Anomaly Detection API (UNCHANGED) ------------------
@app.route("/api/planned_path", methods=["POST"])
def planned_path():
    data = request.json
    user_id = session.get('_id')
    if not user_id:
        return jsonify({"status": "error", "message": "No session ID found."}), 400

    if data and "path" in data:
        database.add_planned_tourist_path(user_id, data["path"])
        user_anomaly_detector = anomaly_detection.AnomalyDetector()
        path_data = [(p['lat'], p['lng']) for p in data["path"]]
        user_anomaly_detector.train(path_data)
        anomaly_detectors[user_id] = user_anomaly_detector
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid path data"}), 400

@app.route("/api/check_anomaly", methods=["POST"])
def check_anomaly():
    data = request.json
    user_id = session.get('_id')
    if not user_id:
        return jsonify({"status": "error", "message": "No session ID found."}), 400

    if not (data and "lat" in data and "lng" in data):
        return jsonify({"status": "error", "message": "Invalid location data"}), 400

    location = (data["lat"], data["lng"])
    user_anomaly_detector = anomaly_detectors.get(user_id)
    all_zones = database.get_all_zones() + external_danger_zones
    
    anomalies = []

    is_approaching, approaching_zone = anomaly_detection.check_approaching_danger_zone(location, all_zones)
    if is_approaching:
        anomalies.append({"type": "approaching_danger_zone", "zone": approaching_zone})
        database.log_anomaly(user_id, "approaching_danger_zone", {"location": location, "zone": approaching_zone})

    is_in_danger, zone = anomaly_detection.check_danger_zone_entry(location, all_zones)
    if is_in_danger:
        anomalies.append({"type": "danger_zone_entry", "zone": zone})
        database.log_anomaly(user_id, "danger_zone_entry", {"location": location, "zone": zone})

    if user_anomaly_detector and user_anomaly_detector.predict(location):
        anomalies.append({"type": "path_deviation"})
        database.log_anomaly(user_id, "path_deviation", {"location": location})

    if anomalies:
        return jsonify({"status": "anomaly", "anomalies": anomalies})
    
    return jsonify({"status": "ok"})

# ------------------ External & Anomaly Detection (UNCHANGED) ------------------
def fetch_external_danger_zones():
    with app.app_context():
        global external_danger_zones
        live_data = external_data.fetch_live_incident_data()
        if live_data:
            external_danger_zones = live_data

def check_for_anomalies():
    with app.app_context():
        latest_locations = database.get_latest_tourist_locations()
        for loc in latest_locations:
            user_id = loc.get("user_id")
            timestamp_val = loc.get('timestamp')
            timestamp = datetime.fromisoformat(timestamp_val.replace('Z', '+00:00')) if isinstance(timestamp_val, str) else timestamp_val
            
            is_inactive, inactive_time = anomaly_detection.check_inactivity(timestamp)
            if is_inactive:
                database.log_anomaly(user_id, "inactivity", {"duration_minutes": inactive_time.total_seconds() / 60})
                print(f"ALERT: User {user_id} has been inactive for {inactive_time}.")

# ------------------ Disaster Prediction API (UNCHANGED) ------------------
@app.route("/api/disaster_zones")
def get_disaster_zones():
    if "admin" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    if not disaster_model.is_trained:
        disaster_model.load_historical_data()
        disaster_model.train()

    return jsonify(disaster_model.get_disaster_zones())

# ------------------ Scheduler & Server Start (UNCHANGED) ------------------
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.add_job(id='FetchExternalData', func=fetch_external_danger_zones, trigger='interval', minutes=1)
scheduler.add_job(id='CheckAnomalies', func=check_for_anomalies, trigger='interval', minutes=1)

if __name__ == '__main__':
    database.initialize_database()
    load_contract() # Load the contract when the app starts
    scheduler.start()
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
