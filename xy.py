# scripts/import_osm_geofences.py
import os, json, requests, time
from osm2geojson import json2geojson
from shapely.geometry import shape, mapping
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()
FIREBASE_CRED = os.getenv("FIREBASE_ADMIN_SDK_JSON")

# Overpass endpoint
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# ---------- change bbox to area of interest ----------
# bbox = south,west,north,east
BBOX = (17.10, 78.00, 17.60, 78.60)  # example for Hyderabad-ish area

# OSM tags to extract (use/extend as needed)
TAG_QUERIES = [
    'way["landuse"="military"]',
    'relation["landuse"="military"]',
    'way["aeroway"="aerodrome"]',
    'relation["aeroway"="aerodrome"]',
    'way["boundary"="protected_area"]',
    'relation["boundary"="protected_area"]',
    'way["boundary"="national_park"]',
    'relation["boundary"="national_park"]'
]

def build_overpass_query(bbox, tags):
    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
    body = "[out:json][timeout:60];(\n"
    for t in tags:
        body += f"  {t}({bbox_str});\n"
    body += ");out body;>;out skel qt;"
    return body

def firestore_init():
    if not firebase_admin._apps:
        if not FIREBASE_CRED:
            raise RuntimeError("FIREBASE_CRED not set in env")
        cred = credentials.Certificate(FIREBASE_CRED)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def ingest_geojson_to_firestore(db, features):
    coll = db.collection("geofences")
    count = 0
    for feature in features["features"]:
        props = feature.get("properties", {})
        geom = feature.get("geometry", None)
        if not geom:
            continue
        shapely_geom = shape(geom)
        # simplify geometry to reduce size (tolerance in degrees)
        sgeom = shapely_geom.simplify(0.0005, preserve_topology=True)
        coords = mapping(sgeom)['coordinates']
        # convert to our polygon list format (lat/lon)
        poly_points = []
        # If it's MultiPolygon, take each polygon as separate fence doc (or store multipolygon)
        if mapping(sgeom)['type'] == "Polygon":
            rings = coords[0]  # exterior ring
            for lon, lat in rings:
                poly_points.append({"lat": float(lat), "lon": float(lon)})
            doc = {
                "name": props.get("name") or props.get("ref") or "OSM geofence",
                "type": "polygon",
                "risk_level": "high",
                "active": True,
                "polygon": poly_points,
                "source": "osm",
                "osm_props": props
            }
            coll.add(doc)
            count += 1
        else:
            # MultiPolygon
            for poly in coords:
                rings = poly[0]
                poly_points = [{"lat": float(lat), "lon": float(lon)} for lon, lat in rings]
                doc = {
                    "name": props.get("name") or props.get("ref") or "OSM geofence",
                    "type": "polygon",
                    "risk_level": "high",
                    "active": True,
                    "polygon": poly_points,
                    "source": "osm",
                    "osm_props": props
                }
                coll.add(doc)
                count += 1
    print("Imported", count, "geofences to Firestore.")

def main():
    print("Building Overpass query for bbox", BBOX)
    q = build_overpass_query(BBOX, TAG_QUERIES)
    print("Querying Overpass (this may take a while)...")
    r = requests.post(OVERPASS_URL, data=q, timeout=120)
    r.raise_for_status()
    osm_json = r.json()
    print("Converting OSM JSON to GeoJSON...")
    geojson = json2geojson(osm_json)
    db = firestore_init()
    ingest_geojson_to_firestore(db, geojson)
    print("Done.")

if __name__ == "__main__":
    main()