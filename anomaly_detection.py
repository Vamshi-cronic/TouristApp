
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import math

# ------------------ Anomaly Detection Model ------------------
class AnomalyDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False

    def train(self, data):
        """
        Train the Isolation Forest model.
        :param data: A list of (latitude, longitude) tuples.
        """
        if len(data) < 2:
            self.is_trained = False
            return

        scaled_data = self.scaler.fit_transform(data)
        self.model.fit(scaled_data)
        self.is_trained = True

    def predict(self, location):
        """
        Predict if a location is an anomaly.
        :param location: A (latitude, longitude) tuple.
        :return: True if the location is an anomaly, False otherwise.
        """
        if not self.is_trained:
            return False

        try:
            scaled_location = self.scaler.transform([location])
            prediction = self.model.predict(scaled_location)
            return prediction[0] == -1
        except Exception as e:
            print(f"Error during anomaly prediction: {e}")
            return False

# ------------------ Anomaly Detection Logic ------------------

def check_inactivity(last_timestamp, inactive_threshold_minutes=5):
    """
    Check if a tourist has been inactive for a long time.
    """
    if not last_timestamp:
        return False, None
    
    now = datetime.now(last_timestamp.tzinfo)
    inactive_threshold = timedelta(minutes=inactive_threshold_minutes)
    
    time_diff = now - last_timestamp
    return time_diff > inactive_threshold, time_diff

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on the earth (specified in decimal degrees).
    """
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371 # Radius of earth in kilometers.
    return c * r

def check_danger_zone_entry(location, danger_zones):
    """
    Check if a tourist has entered a danger zone.
    """
    for zone in danger_zones:
        distance_km = haversine(location[0], location[1], zone['lat'], zone['lng'])
        radius_km = zone['radius'] / 1000
        if distance_km <= radius_km:
            return True, zone
    return False, None

def check_approaching_danger_zone(location, danger_zones, approaching_distance_km=1.0):
    """
    Check if a tourist is approaching a danger zone (within 1km but not inside).
    """
    for zone in danger_zones:
        distance_km = haversine(location[0], location[1], zone['lat'], zone['lng'])
        radius_km = zone['radius'] / 1000
        # Is the user in the 'approaching' buffer?
        is_approaching = distance_km <= radius_km + approaching_distance_km
        # Is the user already inside the zone?
        is_inside = distance_km <= radius_km
        
        if is_approaching and not is_inside:
            return True, zone
    return False, None
