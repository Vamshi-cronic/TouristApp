
import os
import requests
from osm2geojson import json2geojson
from shapely.geometry import shape
import database

# Overpass API endpoint
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Bounding box for the query (e.g., Hyderabad area)
# Format: (south, west, north, east)
BBOX = (17.10, 78.00, 17.60, 78.60)

# OSM tags to identify potential danger zones
TAG_QUERIES = [
    'way["landuse"="military"]',
    'relation["landuse"="military"]',
    'way["amenity"="police"]',
    'relation["amenity"="police"]',
    'way["amenity"="fire_station"]',
    'relation["amenity"="fire_station"]',
]

def build_overpass_query(bbox, tags):
    """Builds the Overpass QL query string."""
    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
    body = "[out:json][timeout:60];(\n"
    for t in tags:
        body += f"  {t}({bbox_str});\n"
    body += ");out body;>;out skel qt;"
    return body

def get_centroid_and_radius(geom):
    """Calculates the centroid and an approximate radius for a shapely geometry."""
    centroid = geom.centroid
    # A simple way to get an "average" radius is to buffer the centroid
    # until its area matches the original polygon's area.
    # A cruder but faster way is to find the max distance to any point.
    if geom.area == 0:
        return None, None
        
    # For simplicity, we'll use a radius derived from the area.
    # radius = sqrt(area / pi)
    # Note: Area is in square degrees, we need to convert to meters.
    # This is a rough approximation. 1 degree lat is ~111km.
    # Area (m^2) approx = Area (deg^2) * (111000^2)
    approx_area_m2 = geom.area * (111000**2)
    radius_m = (approx_area_m2 / 3.14159)**0.5

    return centroid, radius_m

def main():
    """Main function to fetch, process, and import zones."""
    print("Initializing Firebase...")
    database.init_firebase()

    print(f"Clearing existing zones sourced from 'osm'...")
    try:
        database.clear_zones_by_source('osm')
        print("Old OSM zones cleared.")
    except Exception as e:
        print(f"Could not clear zones, may be first run. Error: {e}")


    print(f"Building Overpass query for bounding box: {BBOX}")
    query = build_overpass_query(BBOX, TAG_QUERIES)

    print("Querying Overpass API (this may take a moment)...")
    try:
        response = requests.post(OVERPASS_URL, data=query, timeout=120)
        response.raise_for_status()
        osm_json = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Overpass API: {e}")
        return

    print("Converting OSM JSON to GeoJSON...")
    geojson = json2geojson(osm_json)

    import_count = 0
    print("Processing features and adding to database...")
    for feature in geojson['features']:
        geom = feature.get("geometry")
        props = feature.get("properties")
        if not geom:
            continue

        shapely_geom = shape(geom)
        centroid, radius = get_centroid_and_radius(shapely_geom)

        if not centroid or not radius or radius < 50: # Ignore tiny zones
            continue

        name = props.get("name", "Unnamed Zone")
        landuse = props.get("landuse", "N/A")
        amenity = props.get("amenity", "N/A")
        
        description = f"OSM Imported: {name} (Type: {landuse}/{amenity})"

        try:
            database.add_zone(
                lat=centroid.y,
                lng=centroid.x,
                radius=radius,
                zone_type='osm_imported', # A specific type for these zones
                description=description,
                source='osm' # Add a source tag for easy clearing
            )
            import_count += 1
        except Exception as e:
            print(f"Error adding zone to database: {e}")

    print(f"\nSuccessfully imported {import_count} new zones from OpenStreetMap.")
    print("Update complete.")

if __name__ == "__main__":
    main()
