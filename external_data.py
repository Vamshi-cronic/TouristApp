# external_data.py

import requests
import xml.etree.ElementTree as ET
import os

def fetch_live_incident_data():
    """
    Fetches live disaster alerts for India from the Global Disaster Alert and Coordination System (GDACS).
    
    URL: https://www.gdacs.org/
    
    Returns:
        list: A list of danger zone dictionaries, or an empty list if fetching fails.
    """
    # GDACS RSS feed for active disasters
    base_url = "https://www.gdacs.org/xml/rss.xml"
    
    live_zones = []
    
    # Define namespaces to parse the XML correctly
    namespaces = {
        'georss': 'http://www.georss.org/georss',
        'gdacs': 'http://www.gdacs.org'
    }
    
    try:
        response = requests.get(base_url, timeout=15)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        root = ET.fromstring(response.content)
        
        print("Successfully fetched GDACS RSS feed.")

        for item in root.findall('.//item'):
            # Check if the incident is in India
            country_element = item.find('gdacs:country', namespaces)
            if country_element is not None and country_element.text is not None and 'India' in country_element.text:
                
                title = item.find('title').text
                link = item.find('link').text
                
                # Extract coordinates from the georss:point tag
                point = item.find('georss:point', namespaces)
                if point is not None and point.text:
                    lat_str, lng_str = point.text.split()
                    lat, lng = float(lat_str), float(lng_str)
                    
                    # Use a unique identifier from the link
                    try:
                        guid = link.split('eventid=')[1].split('&')[0]
                    except IndexError:
                        guid = "unknown"

                    live_zones.append({
                        "id": f"ext_gdacs_{guid}",
                        "lat": lat,
                        "lng": lng,
                        "radius": 50000,  # 50km radius for a disaster alert
                        "type": "external",
                        "description": title
                    })

    except requests.exceptions.RequestException as e:
        print(f"Could not fetch live incident data: {e}")
        return [] # Return empty list on failure
    except ET.ParseError as e:
        print(f"Could not parse GDACS RSS feed: {e}")
        return []
        
    #print(f"Found {(live_zones)} relevant alerts for India.")
    return live_zones

def fetch_police_locations_from_api(bbox):
    """Fetches police station locations from the Geoapify Places API."""
    api_key = os.environ.get("GEOAPIFY_API_KEY")
    if not api_key:
        print("Geoapify API key not found in environment variables.")
        return []

    # bbox format: west,south,east,north
    url = f"https://api.geoapify.com/v2/places?categories=service.police&filter=rect:{bbox}&limit=500&apiKey={api_key}"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        police_locations = []
        for feature in data.get("features", []):
            properties = feature.get("properties", {})
            if properties.get("name") and properties.get("lat") and properties.get("lon"):
                police_locations.append({
                    "id": f"geoapify_{properties.get('place_id')}",
                    "unit_name": properties.get("name"),
                    "officer_name": properties.get("name"), # Placeholder, API does not provide officer names
                    "latitude": properties.get("lat"),
                    "longitude": properties.get("lon"),
                    "notes": properties.get("address_line2", "No additional details")
                })
        
        print(f"Fetched {len(police_locations)} police locations from Geoapify.")
        return police_locations
        
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch police locations from Geoapify: {e}")
        return []
    except Exception as e:
        print(f"An error occurred while processing Geoapify data: {e}")
        return []
