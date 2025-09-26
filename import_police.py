
import json
import os
from dotenv import load_dotenv
from firebase_admin import db

# Load environment variables and initialize the database
load_dotenv()
import database

def import_police_data(filepath):
    """
    Reads a JSON file with police location data and adds it to the Firebase database.
    """
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' was not found.")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            police_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. Ensure it is valid.")
        return
    
    if not isinstance(police_data, list):
        print(f"Error: Expected a JSON array (a list of locations), but the format is wrong.")
        return

    print(f"Found {len(police_data)} police units in '{filepath}'.")
    ref = db.reference('police_locations')
    count = 0
    for unit in police_data:
        if all(k in unit for k in ['latitude', 'longitude', 'unit_name']):
            print(f"Adding unit: {unit.get('unit_name', 'Unnamed Unit')}")
            ref.push(unit)
            count += 1
        else:
            print(f"Skipping record due to missing data: {unit}")
    
    print(f"\nImport complete. Added {count} police units to the database.")

if __name__ == "__main__":
    FILE_TO_IMPORT = 'police_locations.json'
    print("--- Starting Police Data Import Script ---")
    import_police_data(FILE_TO_IMPORT)
    print("--- Police Data Import Script Finished ---")
