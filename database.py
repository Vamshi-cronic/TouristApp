
import firebase_admin
from firebase_admin import credentials, db, firestore
import os
import time
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt

# Load environment variables from .env file at the very beginning
load_dotenv()

# --- Firebase Initialization ---
# This block ensures Firebase is initialized once and only once when this module is imported.

# 1. Get credentials from the loaded environment variables.
cred_path = os.environ.get("FIREBASE_ADMIN_SDK_JSON")
database_url = os.environ.get("FIREBASE_DATABASE_URL")

# 2. Provide a clear, critical error if the environment variables are not set.
if not cred_path or not database_url:
    raise ValueError("CRITICAL ERROR: FIREBASE_ADMIN_SDK_JSON and FIREBASE_DATABASE_URL must be set in your .env file.")

# 3. Initialize the Firebase Admin SDK, but only if it hasn't been done already.
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
    except Exception as e:
        # Raise a more informative error if initialization fails for other reasons (e.g., bad JSON file)
        raise RuntimeError(f"Failed to initialize Firebase: {e}. Check your FIREBASE_ADMIN_SDK_JSON path and file content.")

# --- End of Initialization ---

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt()

def initialize_database():
    """
    Checks for the existence of root nodes in the Realtime Database and creates them if they don't exist.
    """
    root_nodes = ["zones", "tourist_locations", "admins", "tourist_paths", "anomaly_alerts"]
    for node in root_nodes:
        if db.reference(node).get() is None:
            db.reference(node).set('')
    print("Firebase Realtime Database checked/initialized.")

def create_admin(username, password):
    """Creates a new admin in the database."""
    admins_ref = db.reference("admins")
    # Check if admin already exists
    existing_admins = admins_ref.order_by_child("username").equal_to(username).get()
    if existing_admins:
        return None
    
    # Use bcrypt and decode to utf-8 for JSON compatibility
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    admin_data = {"username": username, "password_hash": password_hash}
    admins_ref.push(admin_data)
    return admin_data

def get_admin(username):
    """Fetches an admin from the database by username."""
    admins_ref = db.reference("admins")
    admin = admins_ref.order_by_child("username").equal_to(username).limit_to_first(1).get()
    if admin:
        key = list(admin.keys())[0]
        return admin[key]
    return None

def get_all_zones():
    """Fetches all danger zones from the database."""
    zones_ref = db.reference("zones")
    zones_data = zones_ref.get()
    zones = []
    if zones_data and isinstance(zones_data, dict):
        for zone_id, zone in zones_data.items():
            if isinstance(zone, dict):
                zone["id"] = zone_id
                zones.append(zone)
    return zones

def add_zone(lat, lng, radius, description, zone_type='manual', source='manual'):
    """Adds a new danger zone to the database with a description, type, and source."""
    zones_ref = db.reference("zones")
    new_zone = {
        "lat": lat,
        "lng": lng,
        "radius": radius,
        "description": description,
        "type": zone_type,
        "source": source
    }
    new_zone_ref = zones_ref.push(new_zone)
    return new_zone_ref.key

def delete_zone_by_id(zone_id):
    """Deletes a danger zone from the database by its ID."""
    try:
        db.reference(f"zones/{zone_id}").delete()
        return True
    except Exception:
        return False

def clear_zones_by_source(source_tag):
    """Deletes all zones with a specific source tag."""
    zones_ref = db.reference("zones")
    # Query for all zones matching the source tag
    all_zones = zones_ref.order_by_child("source").equal_to(source_tag).get()
    
    if not all_zones:
        return 0 # No zones with that tag found
        
    delete_count = 0
    # The result of the query is a dictionary of key-value pairs
    keys_to_delete = list(all_zones.keys())
    
    for key in keys_to_delete:
        zones_ref.child(key).delete()
        delete_count += 1
        
    return delete_count

def add_tourist_location(user_id, lat, lng, timestamp):
    """Adds a tourist's location to the database."""
    tourist_locations_ref = db.reference("tourist_locations")
    new_location = {
        "user_id": user_id,
        "lat": lat,
        "lng": lng,
        "timestamp": timestamp,
    }
    tourist_locations_ref.push(new_location)

def get_latest_tourist_locations():
    """
    Fetches the most recent location for each unique tourist.
    """
    tourist_locations_ref = db.reference("tourist_locations")
    all_locations = tourist_locations_ref.order_by_child("timestamp").get()
    
    latest_locations = {}
    if all_locations:
        for _, location in all_locations.items():
            user_id = location.get("user_id")
            if user_id:
                latest_locations[user_id] = location # Overwrites older entries, keeping the last one.
            
    return list(latest_locations.values())

def add_planned_tourist_path(user_id, path_data):
    """Adds a planned tourist path to the database."""
    path_ref = db.reference(f"tourist_paths/{user_id}")
    path_ref.set(path_data)

def get_planned_tourist_path(user_id):
    """Retrieves a planned tourist path from the database."""
    path_ref = db.reference(f"tourist_paths/{user_id}")
    return path_ref.get()

def log_anomaly(user_id, anomaly_type, details):
    """Logs a detected anomaly to the database."""
    alerts_ref = db.reference("anomaly_alerts")
    new_alert = {
        "user_id": user_id,
        "type": anomaly_type,
        "details": details,
        "timestamp": time.time()
    }
    alerts_ref.push(new_alert)

def get_tourist_by_aadhaar(aadhaar):
    """Fetches a tourist from the database by Aadhaar number."""
    tourists_ref = db.reference("tourists")
    tourist = tourists_ref.order_by_child("aadhaar").equal_to(aadhaar).limit_to_first(1).get()
    if tourist:
        key = list(tourist.keys())[0]
        return tourist[key]
    return None
