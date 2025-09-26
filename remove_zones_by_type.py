
import database
import sys

def main(zone_type_to_delete):
    """
    Connects to the database and removes all zones with the specified type.
    """
    print(f"Fetching all zones to find and delete zones with type '{zone_type_to_delete}'...")
    all_zones = database.get_all_zones()

    if not all_zones:
        print("No zones found in the database.")
        return

    zones_to_delete = []
    for zone in all_zones:
        if zone.get("type") == zone_type_to_delete:
            zones_to_delete.append(zone)

    if not zones_to_delete:
        print(f"No zones with type '{zone_type_to_delete}' found to delete.")
        return

    print(f"Found {len(zones_to_delete)} zones to delete. Deleting now...")

    deleted_count = 0
    total_to_delete = len(zones_to_delete)
    for zone in zones_to_delete:
        zone_id = zone.get("id")
        if database.delete_zone_by_id(zone_id):
            deleted_count += 1
            # Simple progress indicator
            sys.stdout.write(f"\rDeleted {deleted_count}/{total_to_delete} zones...")
            sys.stdout.flush()
        else:
            # Print newline to avoid messing up the progress indicator
            print(f"\nFailed to delete zone with ID: {zone_id}")

    print(f"\n\nSuccessfully deleted {deleted_count} zones.")
    print("Cleanup complete.")

if __name__ == "__main__":
    # The user specified 'firestore_imported'
    target_type = "firestore_imported"
    main(target_type)
