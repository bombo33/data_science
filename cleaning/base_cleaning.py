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

# Function to normalize times over 24 hours
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

# Basic Statistics
print("Number of stops:", stops.shape[0])
print("Number of routes:", routes.shape[0])
print("Number of trips:", unique_trip_durations['trip_id'].nunique())
print("Average trip duration (minutes):", unique_trip_durations['trip_duration'].mean())
print("Max trip duration (minutes):", unique_trip_durations['trip_duration'].max())
print("Min trip duration (minutes):", unique_trip_durations['trip_duration'].min())
print("Number of short trips (0-20 minutes):", unique_trip_durations[unique_trip_durations['trip_duration'] <= 20].shape[0])

# Plot 1: Distribution of Trip Durations
plt.figure(figsize=(10, 6))
plt.hist(unique_trip_durations['trip_duration'], bins=50, color='blue', edgecolor='black')
plt.title('Distribution of Trip Durations')
plt.xlabel('Duration (minutes)')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()

# Analyze short trips (0-20 minutes)
short_trips = unique_trip_durations[unique_trip_durations['trip_duration'] <= 20]

# Merge short trips with routes and trips data to identify patterns
short_trips_merged = short_trips.merge(trips, on='trip_id').merge(routes, on='route_id')

# Print top routes and trips with short durations
top_short_routes = short_trips_merged['route_id'].value_counts().head(10)
top_short_trips = short_trips_merged['trip_id'].value_counts().head(10)

print("Top routes with short trip durations:\n", top_short_routes)
print("Top trips with short durations:\n", top_short_trips)

# Plot 2: Stop Frequency
stop_frequency = stop_times['stop_id'].value_counts().head(20)  # Show top 20 stops for clarity
plt.figure(figsize=(14, 8))
stop_frequency.plot(kind='bar', color='green')
plt.title('Top 20 Stops by Frequency')
plt.xlabel('Stop ID')
plt.ylabel('Frequency')
plt.xticks(rotation=90)
plt.grid(True)
plt.show()

# Plot 3: Trips per Route
trips_per_route = trips['route_id'].value_counts().head(20)  # Show top 20 routes for clarity
plt.figure(figsize=(14, 8))
trips_per_route.plot(kind='bar', color='purple')
plt.title('Top 20 Routes by Number of Trips')
plt.xlabel('Route ID')
plt.ylabel('Number of Trips')
plt.xticks(rotation=90)
plt.grid(True)
plt.show()

# Plot 4: Geographic Distribution of Stops
plt.figure(figsize=(10, 6))
plt.scatter(stops['stop_lon'], stops['stop_lat'], s=10, c='red', alpha=0.5)
plt.title('Geographic Distribution of Stops')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.grid(True)
plt.show()


