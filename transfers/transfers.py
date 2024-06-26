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
    city_stops = stops_df[stops_df['stop_name'].str.contains(city_name, case=False, na=False, regex=False)]
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

# Example usage for directly reachable destinations:
city_name = "Budapest"
time_limit = pd.Timedelta(hours=5)  # Specify the time limit
direct_reachable_stops_info = find_directly_reachable_destinations_with_times(city_name, time_limit)


def find_second_level_reachable_destinations(direct_reachable_stops_info, time_limit):
    second_level_destinations = pd.DataFrame()

    for _, row in direct_reachable_stops_info.iterrows():
        city_name = row['stop_name']
        additional_travel_time = row['travel_time']
        reachable_from_stop = find_directly_reachable_destinations_with_times(city_name,
                                                                              time_limit - additional_travel_time)

        # Adjust travel times to include the initial travel time
        reachable_from_stop['travel_time'] = reachable_from_stop['travel_time'].apply(
            lambda x: x + additional_travel_time if pd.notnull(x) else x)

        # Exclude cities that are already directly reachable from the starting city
        reachable_from_stop = reachable_from_stop[
            ~reachable_from_stop['stop_id'].isin(direct_reachable_stops_info['stop_id'])]
        second_level_destinations = pd.concat([second_level_destinations, reachable_from_stop])

    return second_level_destinations


# Example usage for second-level reachable destinations:
second_level_reachable_stops_info = find_second_level_reachable_destinations(direct_reachable_stops_info, time_limit)


def visualize_reachable_destinations(city_name, direct_reachable_stops_info, second_level_reachable_stops_info):
    # Get coordinates for the specified city
    city_coords = stops_df[stops_df['stop_name'].str.contains(city_name, case=False, na=False, regex=False)][['stop_lat', 'stop_lon']].values[0].tolist()

    # Create a map centered around the specified city
    map_city = folium.Map(location=city_coords, zoom_start=6)

    # Add markers for directly reachable stops
    for _, row in direct_reachable_stops_info.iterrows():
        stop_coords = [row['stop_lat'], row['stop_lon']]
        popup_info = f"Direct: {row['stop_name']}<br>Travel Time: {row['travel_time']}"
        folium.Marker(location=stop_coords, popup=popup_info, icon=folium.Icon(color='green')).add_to(map_city)

    # Add markers for second-level reachable stops
    for _, row in second_level_reachable_stops_info.iterrows():
        stop_coords = [row['stop_lat'], row['stop_lon']]
        popup_info = f"Second-Level: {row['stop_name']}<br>Travel Time: {row['travel_time']}"
        folium.Marker(location=stop_coords, popup=popup_info, icon=folium.Icon(color='blue')).add_to(map_city)

    map_path = f'all_reachable_from_{city_name.lower()}_map.html'
    map_city.save(map_path)

    return map_city

# Example usage for visualization:
map_city = visualize_reachable_destinations(city_name, direct_reachable_stops_info, second_level_reachable_stops_info)
map_city
