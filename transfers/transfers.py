"""import pandas as pd

# Load data from the uploaded files
agency = pd.read_csv('../gtfs/agency.txt')
calendar = pd.read_csv('../gtfs/calendar.txt')
calendar_dates = pd.read_csv('../gtfs/calendar_dates.txt')
feed_info = pd.read_csv('../gtfs/feed_info.txt')
routes = pd.read_csv('../gtfs/routes.txt')
stops = pd.read_csv('../gtfs/stops.txt')
stop_times = pd.read_csv('../gtfs/stop_times.txt')
transfers = pd.read_csv('../gtfs/transfers.txt')
trips = pd.read_csv('../gtfs/trips.txt')

# Merge stop_times with stops to get stop locations
stop_times_merged = pd.merge(stop_times, stops, on='stop_id')

# Merge trips with routes to get route information
trips_merged = pd.merge(trips, routes, on='route_id')

# Merge stop_times with trips to get complete trip information
trip_details = pd.merge(stop_times_merged, trips_merged, on='trip_id')

# Filter trips starting from a given city (example city: 'Berlin')
city_name = 'Berlin'
starting_stops = stops[stops['stop_name'].str.contains(city_name, case=False)]

# Get trips starting from the selected city's stops
starting_trip_ids = trip_details[trip_details['stop_id'].isin(starting_stops['stop_id'])]['trip_id'].unique()

# Filter stop_times to get the stops for these trips
direct_dest_stops = stop_times_merged[stop_times_merged['trip_id'].isin(starting_trip_ids)][['stop_id', 'stop_name', 'stop_lat', 'stop_lon']].drop_duplicates()

# Remove the starting city stops from the destinations
direct_dest_stops = direct_dest_stops[~direct_dest_stops['stop_id'].isin(starting_stops['stop_id'])]

# Find reachable stops with a given number of transfers
from collections import deque, defaultdict


def bfs_reachable_stops(initial_stops, trip_details, max_transfers=3):
    queue = deque([(stop_id, 0) for stop_id in initial_stops['stop_id'].tolist()])
    transfer_counts = defaultdict(lambda: float('inf'))
    all_reachable_stops = set(initial_stops['stop_id'].tolist())

    while queue:
        current_stop, transfers = queue.popleft()
        if transfers < max_transfers:
            next_trips = trip_details[trip_details['stop_id'] == current_stop]['trip_id']
            next_trip_details = trip_details[trip_details['trip_id'].isin(next_trips)]
            for next_stop in next_trip_details['stop_id'].unique():
                if next_stop not in all_reachable_stops or transfers + 1 < transfer_counts[next_stop]:
                    all_reachable_stops.add(next_stop)
                    transfer_counts[next_stop] = transfers + 1
                    queue.append((next_stop, transfers + 1))

    return all_reachable_stops, transfer_counts


# Combine starting stops with direct destinations to explore further reachable stops
intermediate_stops = pd.concat([starting_stops, direct_dest_stops]).drop_duplicates()

# Find all reachable stops within 2 transfers
reachable_stops, transfer_counts = bfs_reachable_stops(intermediate_stops, trip_details, max_transfers=3)
reachable_stops = reachable_stops - set(direct_dest_stops['stop_id']) - set(starting_stops['stop_id'])

# Get the stops that are indirectly reachable
indirect_dest_stops = stops[stops['stop_id'].isin(reachable_stops)].copy()
indirect_dest_stops.loc[:, 'transfer_count'] = indirect_dest_stops['stop_id'].map(transfer_counts)


import folium
from folium.plugins import MarkerCluster

# Initialize the map centered around the given city
city_coords = starting_stops[['stop_lat', 'stop_lon']].mean()
map_ = folium.Map(location=[city_coords['stop_lat'], city_coords['stop_lon']], zoom_start=5)

# Add marker cluster to handle multiple markers
marker_cluster = MarkerCluster().add_to(map_)

# Add direct destination stops to the map
for _, stop in direct_dest_stops.iterrows():
    popup_text = f"Direct: {stop['stop_name']}"
    folium.Marker(
        location=[stop['stop_lat'], stop['stop_lon']],
        popup=popup_text,
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(marker_cluster)

# Add indirect destination stops to the map with transfer counts
for _, stop in indirect_dest_stops.iterrows():
    popup_text = f"Transfer: {stop['stop_name']}<br>Transfers: {int(stop['transfer_count'])}"
    folium.Marker(
        location=[stop['stop_lat'], stop['stop_lon']],
        popup=popup_text,
        icon=folium.Icon(color='orange', icon='info-sign')
    ).add_to(marker_cluster)

# Display the map
map_.save('trips_and_transfers_map.html')
"""
import math

"""import pandas as pd
from collections import deque, defaultdict

# Load data from the uploaded files
agency = pd.read_csv('../gtfs/agency.txt')
calendar = pd.read_csv('../gtfs/calendar.txt')
calendar_dates = pd.read_csv('../gtfs/calendar_dates.txt')
feed_info = pd.read_csv('../gtfs/feed_info.txt')
routes = pd.read_csv('../gtfs/routes.txt')
stops = pd.read_csv('../gtfs/stops.txt')
stop_times = pd.read_csv('../gtfs/stop_times.txt')
transfers = pd.read_csv('../gtfs/transfers.txt')
trips = pd.read_csv('../gtfs/trips.txt')

# Function to normalize times over 24 hours
def normalize_time(t):
    if pd.isna(t):
        return t
    h, m, s = map(int, t.split(':'))
    return pd.Timedelta(hours=h % 24, minutes=m, seconds=s) + pd.Timedelta(days=h // 24)

# Normalize arrival_time and departure_time
stop_times['arrival_time'] = stop_times['arrival_time'].apply(normalize_time)
stop_times['departure_time'] = stop_times['departure_time'].apply(normalize_time)

# Merge stop_times with stops to get stop locations
stop_times_merged = pd.merge(stop_times, stops, on='stop_id')

# Merge trips with routes to get route information
trips_merged = pd.merge(trips, routes, on='route_id')

# Merge stop_times with trips to get complete trip information
trip_details = pd.merge(stop_times_merged, trips_merged, on='trip_id')

# Filter trips starting from a given city (example city: 'Budapest Népliget')
city_name = 'Budapest Népliget'
starting_stops = stops[stops['stop_name'].str.contains(city_name, case=False)]

# Get trips starting from the selected city's stops
starting_trip_ids = trip_details[trip_details['stop_id'].isin(starting_stops['stop_id'])]['trip_id'].unique()

# Filter stop_times to get the stops for these trips
direct_dest_stops = stop_times_merged[stop_times_merged['trip_id'].isin(starting_trip_ids)][
    ['trip_id', 'stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'arrival_time', 'departure_time', 'stop_sequence']].drop_duplicates()

# Remove the starting city stops from the destinations
direct_dest_stops = direct_dest_stops[~direct_dest_stops['stop_id'].isin(starting_stops['stop_id'])]

# Calculate travel times between stops on each trip
def calculate_travel_times(stop_times):
    stop_times = stop_times.sort_values(by=['trip_id', 'stop_sequence'])
    stop_times['next_departure'] = stop_times.groupby('trip_id')['departure_time'].shift(-1)
    stop_times['travel_time'] = (stop_times['next_departure'] - stop_times['departure_time']).dt.total_seconds() / 60
    stop_times['travel_time'] = stop_times['travel_time'].fillna(0)  # Fill NaNs with 0 for the last stop in each trip
    return stop_times

stop_times = calculate_travel_times(stop_times)

# Pre-filter direct destinations by travel time
direct_dest_travel_times = stop_times.groupby('trip_id')['travel_time'].sum().reset_index()
direct_dest_stops = pd.merge(direct_dest_stops, direct_dest_travel_times, on='trip_id')
direct_dest_stops = direct_dest_stops[direct_dest_stops['travel_time'] <= 200]
# Remove duplicate stops, keeping the one with the shortest travel time
direct_dest_stops = direct_dest_stops.sort_values(by='travel_time').drop_duplicates(subset='stop_id', keep='first')
direct_dest_stops.to_csv('direct_dest_stops.csv', index=False)

# Find reachable stops with a given number of transfers and within a travel time limit
def bfs_reachable_stops(initial_stops, trip_details, stop_times, max_transfers=1, max_travel_time=120):
    queue = deque([(stop_id, 0, 0) for stop_id in initial_stops['stop_id'].tolist()])
    transfer_counts = defaultdict(lambda: float('inf'))
    travel_times = defaultdict(lambda: float('inf'))
    all_reachable_stops = set(initial_stops['stop_id'].tolist())

    while queue:
        current_stop, transfers, accumulated_time = queue.popleft()
        print("Next in queue\n")
        print(current_stop, transfers, accumulated_time)
        if transfers < max_transfers and accumulated_time < max_travel_time:
            next_trips = trip_details[trip_details['stop_id'] == current_stop]
            for _, trip in next_trips.iterrows():
                next_stop = trip['stop_id']
                trip_id = trip['trip_id']
                stop_sequence = trip['stop_sequence']
                trip_times = stop_times[(stop_times['trip_id'] == trip_id) & (stop_times['stop_sequence'] >= stop_sequence)]
                travel_time = trip_times['travel_time'].sum()

                total_travel_time = accumulated_time + travel_time
                if total_travel_time > max_travel_time:
                    continue

                if next_stop not in all_reachable_stops or transfers + 1 < transfer_counts[next_stop] or total_travel_time < travel_times[next_stop]:
                    all_reachable_stops.add(next_stop)
                    transfer_counts[next_stop] = transfers + 1
                    travel_times[next_stop] = total_travel_time
                    queue.append((next_stop, transfers + 1, total_travel_time))

    return all_reachable_stops, transfer_counts, travel_times

# Combine starting stops with direct destinations to explore further reachable stops
intermediate_stops = pd.concat([starting_stops, direct_dest_stops]).drop_duplicates()
intermediate_stops.to_csv('intermediate_stops.csv', index=False)

# Find all reachable stops within 3 transfers and 120 minutes
reachable_stops, transfer_counts, travel_times = bfs_reachable_stops(intermediate_stops, trip_details, stop_times, max_transfers=2, max_travel_time=200)
reachable_stops = reachable_stops - set(direct_dest_stops['stop_id']) - set(starting_stops['stop_id'])

# Get the stops that are indirectly reachable
indirect_dest_stops = stops[stops['stop_id'].isin(reachable_stops)].copy()
indirect_dest_stops.loc[:, 'transfer_count'] = indirect_dest_stops['stop_id'].map(transfer_counts)
indirect_dest_stops.loc[:, 'travel_time'] = indirect_dest_stops['stop_id'].map(travel_times)

# Visualization on a map
import folium
from folium.plugins import MarkerCluster

# Initialize the map centered around the given city
city_coords = starting_stops[['stop_lat', 'stop_lon']].mean()
map_ = folium.Map(location=[city_coords['stop_lat'], city_coords['stop_lon']], zoom_start=5)

# Add marker cluster to handle multiple markers
marker_cluster = MarkerCluster().add_to(map_)

# Add direct destination stops to the map
for _, stop in direct_dest_stops.iterrows():
    popup_text = f"Direct: {stop['stop_name']}"
    folium.Marker(
        location=[stop['stop_lat'], stop['stop_lon']],
        popup=popup_text,
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(marker_cluster)

# Add indirect destination stops to the map with transfer counts and travel time
for _, stop in indirect_dest_stops.iterrows():
    popup_text = f"Transfer: {stop['stop_name']}<br>Transfers: {int(stop['transfer_count'])}<br>Travel Time: {int(stop['travel_time'])} minutes"
    folium.Marker(
        location=[stop['stop_lat'], stop['stop_lon']],
        popup=popup_text,
        icon=folium.Icon(color='orange', icon='info-sign')
    ).add_to(marker_cluster)

# Display the map
map_.save('trips_and_transfers_map.html')
"""

import pandas as pd
import folium

# Load data from the uploaded files
agency = pd.read_csv('../gtfs/agency.txt')
calendar = pd.read_csv('../gtfs/calendar.txt')
calendar_dates = pd.read_csv('../gtfs/calendar_dates.txt')
feed_info = pd.read_csv('../gtfs/feed_info.txt')
routes_df = pd.read_csv('../gtfs/routes.txt')
stops_df = pd.read_csv('../gtfs/stops.txt')
stop_times_df = pd.read_csv('../gtfs/stop_times.txt')
transfers = pd.read_csv('../gtfs/transfers.txt')
trips_df = pd.read_csv('../gtfs/trips.txt')

def normalize_time(t):
    if pd.isna(t):
        return t
    h, m, s = map(int, t.split(':'))
    return pd.Timedelta(hours=h % 24, minutes=m, seconds=s) + pd.Timedelta(days=h // 24)

# Normalize arrival_time and departure_time
stop_times_df['arrival_time'] = stop_times_df['arrival_time'].apply(normalize_time)
stop_times_df['departure_time'] = stop_times_df['departure_time'].apply(normalize_time)

def find_directly_reachable_destinations_with_times(city_name, time_limit):
    # Step 1: Identify stop ID(s) for the specified city
    city_stops = stops_df[stops_df['stop_name'].str.contains(city_name, case=False, na=False)]
    city_stop_ids = city_stops['stop_id'].tolist()

    # Step 2: Find trips containing the specified city
    city_trips = stop_times_df[stop_times_df['stop_id'].isin(city_stop_ids)]
    city_trip_ids = city_trips['trip_id'].tolist()

    # Step 3: Determine subsequent stops and calculate travel and stop times
    travel_times = []
    stop_times = []

    for trip_id in city_trip_ids:
        trip_stop_times = stop_times_df[stop_times_df['trip_id'] == trip_id].sort_values('stop_sequence').reset_index(drop=True)
        start_index = trip_stop_times[trip_stop_times['stop_id'].isin(city_stop_ids)].index[0]

        cumulative_travel_time = pd.Timedelta(0)

        for i in range(start_index + 1, len(trip_stop_times)):
            prev_stop = trip_stop_times.iloc[i - 1]
            current_stop = trip_stop_times.iloc[i]
            travel_time = current_stop['arrival_time'] - prev_stop['departure_time']
            cumulative_travel_time += travel_time

            if cumulative_travel_time > time_limit:
                break

            travel_times.append((current_stop['stop_id'], cumulative_travel_time))
            stop_time = current_stop['departure_time'] - current_stop['arrival_time']
            stop_times.append((current_stop['stop_id'], stop_time))

    # Get unique stop IDs for directly reachable destinations
    reachable_stop_ids = list(set([stop[0] for stop in travel_times]))
    reachable_stops_info = stops_df[stops_df['stop_id'].isin(reachable_stop_ids) & (~stops_df['stop_id'].isin(city_stop_ids))][['stop_id', 'stop_name', 'stop_lat', 'stop_lon']]

    # Adding travel and stop times to the dataframe
    travel_time_dict = dict(travel_times)
    stop_time_dict = dict(stop_times)

    reachable_stops_info['travel_time'] = reachable_stops_info['stop_id'].map(travel_time_dict)
    reachable_stops_info['stop_time'] = reachable_stops_info['stop_id'].map(stop_time_dict)

    return reachable_stops_info

def visualize_reachable_destinations(city_name, reachable_stops_info):
    # Get coordinates for the specified city
    city_coords = stops_df[stops_df['stop_name'].str.contains(city_name, case=False, na=False)][['stop_lat', 'stop_lon']].values[0].tolist()

    # Create a map centered around the specified city
    map_city = folium.Map(location=city_coords, zoom_start=6)

    # Add markers for directly reachable stops
    for _, row in reachable_stops_info.iterrows():
        stop_coords = [row['stop_lat'], row['stop_lon']]
        popup_info = f"{row['stop_name']}<br>Travel Time: {row['travel_time']}"
        folium.Marker(location=stop_coords, popup=popup_info).add_to(map_city)

    map_path = f'directly_reachable_from_{city_name.lower()}_map.html'
    map_city.save(map_path)

    return map_path

# Example usage:
city_name = "Budapest"
time_limit = pd.Timedelta(hours=5)  # Specify the time limit
reachable_stops_info = find_directly_reachable_destinations_with_times(city_name, time_limit)
visualize_reachable_destinations(city_name, reachable_stops_info)



