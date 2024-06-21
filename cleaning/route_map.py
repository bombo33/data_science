import pandas as pd
import numpy as np
from datetime import timedelta, datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def parse_time(time_str):
    """Parse a time string in the format HH:MM:SS to a datetime object, handling hours > 23."""
    hours, minutes, seconds = map(int, time_str.split(':'))
    if hours >= 24:
        days, hours = divmod(hours, 24)
        return datetime.strptime(f'{hours:02}:{minutes:02}:{seconds:02}', '%H:%M:%S') + timedelta(days=days)
    else:
        return datetime.strptime(time_str, '%H:%M:%S')

# Load the data
stops_df = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/stops.txt')
routes_df = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/routes.txt')
trips_df = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/trips.txt')
stop_times_df = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/stop_times.txt')
calendar_df = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/calendar.txt')
transfers_df = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/transfers.txt')

# Parse arrival and departure times correctly
stop_times_df['arrival_time'] = stop_times_df['arrival_time'].apply(parse_time)
stop_times_df['departure_time'] = stop_times_df['departure_time'].apply(parse_time)


# Calculate trip durations and filter trips based on constraints
def calculate_trip_durations(max_time, max_changes, start_time):
    trip_durations = stop_times_df.groupby('trip_id').agg(
        {'arrival_time': 'max', 'departure_time': 'min'}).reset_index()
    trip_durations['duration'] = trip_durations['arrival_time'] - trip_durations['departure_time']
    trip_durations = trip_durations[trip_durations['duration'] < timedelta(hours=max_time)]

    # Create a datetime object for the travel time using a default date
    start_datetime = datetime.combine(datetime.today(), start_time)

    # Filter trips based on the start time
    trip_durations = trip_durations[
        (stop_times_df['departure_time'] >= start_datetime) &
        (stop_times_df['departure_time'] < start_datetime + timedelta(hours=1))
        ]

    return trip_durations


# Streamlit UI
st.title('FlixBus Data Visualization')

# Tabs for different visualizations
tabs = st.tabs(['Reachable Destinations', 'Service Heatmap', 'Bus Frequency'])

with tabs[0]:
    st.subheader('Reachable Destinations')
    start_stop = st.selectbox('Select Start Stop', stops_df['stop_name'].unique())
    max_time = st.slider('Maximum Travel Time (hours)', 1, 12, 4)
    max_changes = st.slider('Maximum Changes', 0, 3, 1)
    travel_time = st.time_input('Preferred Travel Time', value=datetime.now().time())

    if st.button('Show Reachable Destinations'):
        start_stop_ids = stops_df[stops_df['stop_name'].str.contains(start_stop, case=False, na=False)][
            'stop_id'].tolist()

        if start_stop_ids:
            trip_durations = calculate_trip_durations(max_time, max_changes, travel_time)
            reachable_stops = stop_times_df[stop_times_df['trip_id'].isin(trip_durations['trip_id'])]
            reachable_coords = stops_df[stops_df['stop_id'].isin(reachable_stops['stop_id'])]

            # Map visualization
            fig = px.scatter_mapbox(
                reachable_coords,
                lat="stop_lat",
                lon="stop_lon",
                text="stop_name",
                zoom=10,
                height=600
            )
            fig.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig)

            # List of trips
            reachable_stops_details = reachable_stops.merge(stops_df, on='stop_id')
            st.write(reachable_stops_details[['stop_name', 'arrival_time', 'departure_time']])
        else:
            st.write('No reachable destinations found.')

with tabs[1]:
    st.subheader('Service Heatmap')
    # Aggregate data for heatmap
    stop_times_df['hour'] = stop_times_df['arrival_time'].dt.hour
    stop_frequency = stop_times_df.groupby('stop_id').size().reset_index(name='count')
    stop_data = stop_frequency.merge(stops_df, on='stop_id')

    # Generate heatmap
    fig = px.density_mapbox(
        stop_data,
        lat='stop_lat',
        lon='stop_lon',
        z='count',
        radius=10,
        center=dict(lat=stop_data['stop_lat'].mean(), lon=stop_data['stop_lon'].mean()),
        zoom=5,
        mapbox_style='stamen-terrain'
    )
    st.plotly_chart(fig)

with tabs[2]:
    st.subheader('Bus Frequency at a Stop')
    stop_name = st.selectbox('Select Stop', stops_df['stop_name'].unique())

    if st.button('Show Frequency'):
        selected_stop_id = \
        stops_df[stops_df['stop_name'].str.contains(stop_name, case=False, na=False)]['stop_id'].values[0]
        stop_frequency = stop_times_df[stop_times_df['stop_id'] == selected_stop_id].groupby(
            stop_times_df['arrival_time'].dt.hour).size().reset_index(name='count')

        fig = px.bar(stop_frequency, x='arrival_time', y='count',
                     labels={'arrival_time': 'Hour of Day', 'count': 'Number of Buses'})
        st.plotly_chart(fig)

