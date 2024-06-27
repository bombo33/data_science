import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# Set page config at the beginning
st.set_page_config(layout="wide")

# Set base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Construct file paths
stops_path = os.path.join(base_dir, '..', 'gtfs', 'stops.txt')
stop_times_path = os.path.join(base_dir, '..', 'gtfs', 'stop_times.txt')
agency_path = os.path.join(base_dir, '..', 'gtfs', 'agency.txt')
calendar_path = os.path.join(base_dir, '..', 'gtfs', 'calendar.txt')
calendar_dates_path = os.path.join(base_dir, '..', 'gtfs', 'calendar_dates.txt')
feed_info_path = os.path.join(base_dir, '..', 'gtfs', 'feed_info.txt')
routes_path = os.path.join(base_dir, '..', 'gtfs', 'routes.txt')
transfers_path = os.path.join(base_dir, '..', 'gtfs', 'transfers.txt')
trips_path = os.path.join(base_dir, '..', 'gtfs', 'trips.txt')

# Load data from the uploaded files
@st.cache_data
def load_data():
    agency = pd.read_csv(agency_path)
    calendar = pd.read_csv(calendar_path)
    calendar_dates = pd.read_csv(calendar_dates_path)
    feed_info = pd.read_csv(feed_info_path)
    routes_df = pd.read_csv(routes_path)
    stops_df = pd.read_csv(stops_path)
    stop_times_df = pd.read_csv(stop_times_path)
    transfers = pd.read_csv(transfers_path)
    trips_df = pd.read_csv(trips_path)
    return stops_df, stop_times_df, routes_df

stops_df, stop_times_df, routes_df = load_data()

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
    if city_stops.empty:
        return pd.DataFrame()  # Return an empty DataFrame if no stops are found

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

    # Convert Timedelta columns to string
    reachable_stops_info['travel_time'] = reachable_stops_info['travel_time'].astype(str)
    reachable_stops_info['stop_time'] = reachable_stops_info['stop_time'].astype(str)

    return reachable_stops_info

def visualize_reachable_destinations(city_name, reachable_stops_info):
    if reachable_stops_info.empty:
        st.warning("No stops found for the specified city.")
        return None

    # Get coordinates for the specified city
    city_coords = stops_df[stops_df['stop_name'].str.contains(city_name, case=False, na=False)][['stop_lat', 'stop_lon']].values[0].tolist()

    # Create a map centered around the specified city
    map_city = folium.Map(location=city_coords, zoom_start=6)

    # Add markers for directly reachable stops
    for _, row in reachable_stops_info.iterrows():
        stop_coords = [row['stop_lat'], row['stop_lon']]
        popup_info = f"{row['stop_name']}<br>Travel Time: {row['travel_time']}"
        folium.Marker(location=stop_coords, popup=popup_info, tooltip=row['stop_id']).add_to(map_city)

    return map_city

# Streamlit interface
st.title("Trip and Transfer Visualization")

# Input for city name and time limit
city_name = st.text_input("Enter a city name:", "Budapest")
time_limit_hours = st.number_input("Enter the time limit in hours:", min_value=1, max_value=24, value=5)
time_limit = pd.Timedelta(hours=time_limit_hours)

# Button to trigger fetching of data
if st.button("Find Trips"):
    reachable_stops_info = find_directly_reachable_destinations_with_times(city_name, time_limit)
    st.session_state['reachable_stops_info'] = reachable_stops_info
    map_city = visualize_reachable_destinations(city_name, reachable_stops_info)
    st.session_state['map_city'] = map_city
    st.session_state['selected_trip'] = None
else:
    reachable_stops_info = st.session_state.get('reachable_stops_info', pd.DataFrame())
    map_city = st.session_state.get('map_city', None)

# Display the map and trip list with details box
col1, col2 = st.columns([2, 1])

with col1:
    if map_city:
        st_data = st_folium(map_city, width=900, height=700, returned_objects=["last_object_clicked"])

        # Capture click event from the map
        if "last_object_clicked" in st_data and st_data["last_object_clicked"] is not None:
            if "tooltip" in st_data["last_object_clicked"]:
                clicked_stop_id = st_data["last_object_clicked"]["tooltip"]
                selected_trip = reachable_stops_info[reachable_stops_info['stop_id'] == clicked_stop_id].iloc[0]
                st.session_state['selected_trip'] = selected_trip

# Display details box
if 'selected_trip' in st.session_state and st.session_state['selected_trip'] is not None:
    selected_trip = st.session_state['selected_trip']
    st.write("### Selected Trip Details")
    st.markdown(f"""
        **Stop Name:** {selected_trip['stop_name']}  
        **Stop Latitude:** {selected_trip['stop_lat']}  
        **Stop Longitude:** {selected_trip['stop_lon']}  
        **Travel Time:** {selected_trip['travel_time']}  
        **Stop Time:** {selected_trip['stop_time']}
    """)

with col2:
    if not reachable_stops_info.empty:
        st.write("## List of Trips")
        trip_list = reachable_stops_info[['stop_name', 'travel_time']].reset_index(drop=True)

        # Capture click event from the list
        def display_trip_details(row):
            st.session_state['selected_trip'] = reachable_stops_info.loc[row.name]
            return None

        for idx, row in trip_list.iterrows():
            if st.button(row['stop_name'], key=row['stop_name']):
                display_trip_details(row)