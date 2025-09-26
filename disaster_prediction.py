
import json
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import numpy as np
from datetime import datetime, timedelta

class DisasterPredictionModel:
    def __init__(self, eps=0.3, min_samples=2): # Changed min_samples to 2
        self.model = DBSCAN(eps=eps, min_samples=min_samples)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.historical_data = []

    def load_historical_data(self, file_path='historical_disasters.json'):
        """Loads historical disaster data from a JSON file.""" 
        with open(file_path, 'r') as f:
            self.historical_data = json.load(f)

    def train(self):
        """Trains the DBSCAN model on historical disaster locations."""
        if not self.historical_data:
            self.is_trained = False
            return

        locations = [d['place'] for d in self.historical_data]
        if len(locations) < self.model.min_samples:
            self.is_trained = False
            return

        locations_array = np.array([[loc['lat'], loc['lng']] for loc in locations])

        scaled_locations = self.scaler.fit_transform(locations_array)
        self.model.fit(scaled_locations)
        self.is_trained = True

    def _predict_next_occurrence(self, cluster_indices):
        """Predicts the next occurrence based on historical frequency."""
        cluster_events = [self.historical_data[i] for i in cluster_indices]
        
        for event in cluster_events:
            event['datetime'] = datetime.strptime(f"{event['date']} {event['time']}", '%Y-%m-%d %H:%M:%S')
        cluster_events.sort(key=lambda x: x['datetime'])

        if len(cluster_events) > 1:
            time_deltas = [(cluster_events[i+1]['datetime'] - cluster_events[i]['datetime']).total_seconds() for i in range(len(cluster_events) - 1)]
            avg_delta_seconds = np.mean(time_deltas)
            avg_delta = timedelta(seconds=avg_delta_seconds)
        else:
            avg_delta = timedelta(days=365)

        last_event_time = cluster_events[-1]['datetime']
        predicted_datetime = last_event_time + avg_delta

        seconds_from_midnight = [e['datetime'].time().hour * 3600 + e['datetime'].time().minute * 60 + e['datetime'].time().second for e in cluster_events]
        avg_seconds = int(np.mean(seconds_from_midnight))
        avg_time = (datetime.min + timedelta(seconds=avg_seconds)).time()

        predicted_datetime = predicted_datetime.replace(hour=avg_time.hour, minute=avg_time.minute, second=avg_time.second)

        return predicted_datetime

    def get_disaster_zones(self, probability_threshold=0.2):
        """
        Identifies and predicts future disaster-prone zones with realistic timing.
        """
        if not self.is_trained or not self.historical_data:
            return []

        zones = []
        labels = self.model.labels_
        unique_labels = set(labels)

        locations = np.array([[d['place']['lat'], d['place']['lng']] for d in self.historical_data])

        for label in unique_labels:
            if label == -1:
                continue

            cluster_indices = np.where(labels == label)[0]
            if len(cluster_indices) > 0:
                cluster_points = locations[cluster_indices]
                centroid = np.mean(cluster_points, axis=0)

                sample_event = self.historical_data[cluster_indices[0]]

                # New probability calculation
                probability = min(1.0, len(cluster_points) / 10.0)

                if probability >= probability_threshold:
                    predicted_datetime = self._predict_next_occurrence(cluster_indices)
                    
                    if predicted_datetime > datetime.now():
                        zones.append({
                            'lat': centroid[0],
                            'lng': centroid[1],
                            'description': f"Predicted high risk of '{sample_event['description']}'. Chance of occurence: {probability:.0%}",
                            'prob': probability,
                            'date': predicted_datetime.strftime('%Y-%m-%d'),
                            'time': predicted_datetime.strftime('%H:%M:%S')
                        })
        return zones
