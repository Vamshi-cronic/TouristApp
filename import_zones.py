
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Now import the database module which relies on those env vars
import database

def import_zones_from_file(filepath):
    """
    Reads a JSON file with zone data and adds it to the Firebase database.
    """
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' was not found.")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            zones_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. Please ensure it is a valid JSON file.")
        return
    
    if not isinstance(zones_data, list):
        print(f"Error: Expected a JSON array (a list of zones), but the file format is different.")
        return

    #print(f"Found {len(zones_data)} zones in '{filepath}'.")

    count = 0
    for zone in zones_data:
        # Check for the required fields in each zone object
        if all(k in zone for k in ['latitude', 'longitude', 'radius_m', 'notes']):
            print(f"Adding zone: {zone.get('zone_name', 'Unnamed Zone')}")
            database.add_zone(
                lat=zone['latitude'],
                lng=zone['longitude'],
                radius=zone['radius_m'],
                description=zone.get('notes', '')
            )
            count += 1
        else:
            print(f"Skipping record due to missing data: {zone}")
    
    print(f"\nImport complete. Added {count} zones to the database.")

if __name__ == "__main__":
    FILE_TO_IMPORT = 'india_zones_dataset.json'
    print("--- Starting Zone Import Script ---")
    # The database module handles its own initialization
    import_zones_from_file(FILE_TO_IMPORT)
    print("--- Zone Import Script Finished ---")
