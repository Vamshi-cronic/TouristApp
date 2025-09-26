
import database
from firebase_admin import firestore
from shapely.geometry import Polygon

def get_centroid_and_radius(polygon_points):
    """Calculates the centroid and an approximate radius for a list of points."""
    if len(polygon_points) < 3:
        return None, None

    polygon = Polygon(polygon_points)
    centroid = polygon.centroid
    
    # Approximate radius based on the area of the polygon
    if polygon.area == 0:
        return None, None

    # Area is in square degrees, needs a rough conversion to meters.
    # 1 degree of latitude is ~111.1 km.
    # This is a simplification and is most accurate near the equator.
    approx_area_m2 = polygon.area * (111100**2)
    radius_m = (approx_area_m2 / 3.14159)**0.5

    # Ignore zones that are too small to be meaningful
    if radius_m < 50:
        return None, None

    return centroid, radius_m

def main():
    """Main function to fetch from Firestore and save to Realtime DB."""
    # The database is now initialized automatically when the database module is imported.
    print("Firebase initialized automatically.")

    print("Getting Firestore client...")
    db_firestore = firestore.client()

    print("Clearing previously imported zones from Realtime DB...")
    source_tag = 'firestore_import'
    cleared_count = database.clear_zones_by_source(source_tag)
    print(f"Cleared {cleared_count} old zones.")

    print("Fetching geofences from Firestore collection 'geofences'...")
    geofences_ref = db_firestore.collection("geofences")
    docs = geofences_ref.stream()

    import_count = 0
    for doc in docs:
        zone_data = doc.to_dict()
        polygon_data = zone_data.get("polygon")

        if not polygon_data or not isinstance(polygon_data, list) or len(polygon_data) < 3:
            continue

        # Convert [{"lat": y, "lon": x}] to [(x, y)] for Shapely
        try:
            polygon_points = [(p["lon"], p["lat"]) for p in polygon_data]
        except (KeyError, TypeError):
            print(f"Skipping zone with malformed polygon data: {doc.id}")
            continue

        centroid, radius = get_centroid_and_radius(polygon_points)

        if not centroid or not radius:
            continue
        
        name = zone_data.get("name", "Unnamed Zone from Firestore")
        description = f"Imported from Firestore: {name}"

        try:
            database.add_zone(
                lat=centroid.y,
                lng=centroid.x,
                radius=radius,
                description=description,
                zone_type='firestore_imported',
                source=source_tag
            )
            import_count += 1
        except Exception as e:
            print(f"Error adding zone to Realtime DB: {e}")

    print(f"\nSuccessfully imported {import_count} new zones from Firestore to Realtime DB.")
    print("Update complete.")

if __name__ == "__main__":
    main()
