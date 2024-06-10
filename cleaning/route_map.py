import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from folium.plugins import MarkerCluster


# Load the data
stops = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/stops.txt')
routes = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/routes.txt')
trips = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/trips.txt')
stop_times = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/stop_times.txt')
calendar = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/calendar.txt')

# Function to normalize times over 24 hours without losing trip length
def normalize_time(t):
    if pd.isna(t):
        return t
    h, m, s = map(int, t.split(':'))
    return pd.Timedelta(hours=h, minutes=m, seconds=s)

# Apply normalization to times
stop_times['arrival_time'] = stop_times['arrival_time'].apply(normalize_time)
stop_times['departure_time'] = stop_times['departure_time'].apply(normalize_time)

# Ensure trip IDs are correctly sorted by stop_sequence to aggregate segments
stop_times = stop_times.sort_values(by=['trip_id', 'stop_sequence'])

# Calculate trip durations by aggregating segments
stop_times['trip_start'] = stop_times.groupby('trip_id')['departure_time'].transform('first')
stop_times['trip_end'] = stop_times.groupby('trip_id')['arrival_time'].transform('last')

stop_times['trip_duration'] = (stop_times['trip_end'] - stop_times['trip_start']).dt.total_seconds() / 60

# Handle trips spanning multiple days
stop_times['trip_duration'] = stop_times['trip_duration'].apply(lambda x: x if x >= 0 else x + 1440)

# Remove unrealistic durations (assuming max 48 hours)
stop_times = stop_times[(stop_times['trip_duration'] >= 0) & (stop_times['trip_duration'] <= 2880)]

# Drop duplicate rows to keep only unique trip durations
unique_trip_durations = stop_times.drop_duplicates(subset=['trip_id', 'trip_duration'])

# Filter routes under a certain duration (e.g., 60 minutes)
max_duration = 60
short_duration_routes = unique_trip_durations[unique_trip_durations['trip_duration'] <= max_duration]

# Merge short duration trips with routes and trips data
short_duration_routes = short_duration_routes.merge(trips, on='trip_id').merge(routes, on='route_id')

# Get the list of relevant trip IDs and their corresponding stop_times
relevant_trip_ids = short_duration_routes['trip_id'].unique()
relevant_stop_times = stop_times[stop_times['trip_id'].isin(relevant_trip_ids)]

# Merge stop times with stops to get geographic coordinates
relevant_stop_times = relevant_stop_times.merge(stops, on='stop_id')

# Initialize a map centered around a general location (e.g., Europe)
map_center = [50.1109, 8.6821]  # Coordinates for Frankfurt, Germany
m = folium.Map(location=map_center, zoom_start=6)

# Add routes to the map
for trip_id in relevant_trip_ids:
    trip_stops = relevant_stop_times[relevant_stop_times['trip_id'] == trip_id]
    trip_coordinates = list(zip(trip_stops['stop_lat'], trip_stops['stop_lon']))
    folium.PolyLine(trip_coordinates, color='blue', weight=2.5, opacity=1).add_to(m)

# Add stops to the map with a marker cluster
marker_cluster = MarkerCluster().add_to(m)
for idx, stop in stops.iterrows():
    folium.Marker(location=[stop['stop_lat'], stop['stop_lon']], popup=stop['stop_name']).add_to(marker_cluster)

# Save the map to an HTML file
output_dir = '/home/anatol/Documents/2023_24_2/DS/data'
output_file = 'filtered_routes_map.html'
os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist
m.save(os.path.join(output_dir, output_file))
