def destinations_interface_main():
    import os
    import streamlit as st
    import pandas as pd
    import folium
    from streamlit_folium import st_folium
    import folium.plugins as plugins
    import branca.colormap as cm
    from matplotlib.colors import to_rgba
    import numpy as np

    # Define time interval labels
    time_interval_labels = {
        'all_day': 'All Day',
        'early_morning': 'Early Morning (00:00 - 06:00)',
        'morning': 'Morning (06:00 - 10:00)',
        'midday': 'Midday (10:00 - 14:00)',
        'afternoon': 'Afternoon (14:00 - 18:00)',
        'late_afternoon': 'Late Afternoon (18:00 - 21:00)',
        'night': 'Night (21:00 - 00:00)'
    }

    # Ensure initial values are set in session state
    if 'city_name' not in st.session_state:
        st.session_state['city_name'] = "Budapest"
    if 'max_travel_hours' not in st.session_state:
        st.session_state['max_travel_hours'] = 5
    if 'max_changes' not in st.session_state:
        st.session_state['max_changes'] = 1
    if 'time_interval' not in st.session_state:
        st.session_state['time_interval'] = 'morning'

    def interpolate_color(color1, color2, fraction):
        rgba1 = np.array(to_rgba(color1))
        rgba2 = np.array(to_rgba(color2))
        interpolated_rgba = rgba1 + (rgba2 - rgba1) * fraction
        return '#{:02x}{:02x}{:02x}'.format(
            int(interpolated_rgba[0] * 255),
            int(interpolated_rgba[1] * 255),
            int(interpolated_rgba[2] * 255)
        )

    # st.set_page_config(layout="wide")

    # Capture scroll position using JavaScript and store it in session storage
    st.markdown("""
        <script>
        function storeScroll() {
            var scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
            window.sessionStorage.setItem("scrollPosition", scrollPosition);
        }
        window.onscroll = storeScroll;
        </script>
    """, unsafe_allow_html=True)

    # Retrieve scroll position from session storage and set it on page load
    st.markdown(f"""
        <script>
        window.onload = function() {{
            var scrollPosition = window.sessionStorage.getItem("scrollPosition");
            if (scrollPosition !== null) {{
                window.scrollTo(0, parseInt(scrollPosition));
            }}
        }}
        </script>
    """, unsafe_allow_html=True)

    # Set base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))

    precomputed_data_path = os.path.join(base_dir, 'precomputed_routes_adjusted_test.csv')

    def get_color(travel_time_hours, min_hours, max_hours):
        colormap = cm.linear.YlOrRd_09.scale(min_hours, max_hours)
        return colormap(travel_time_hours)


    def get_legend_html(min_hours, max_hours, width=1200):
        intervals = [min_hours + (i * (max_hours - min_hours) / 9) for i in range(10)]
        colors = [get_color(interval, min_hours, max_hours) for interval in intervals]

        gradient_css = "background: linear-gradient(to right, " + ", ".join(colors) + ");"

        labels_html = "".join(
            f'<div style="flex: 1; text-align: center; font-size: 14px;">{interval:.1f}</div>'
            for interval in intervals
        )

        legend_html = f"""
        <div style="display: flex; flex-direction: column; align-items: center; padding: 3px; border: 1px solid black; border-radius: 3px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.2); width: {width}px; background-color: black;">
            <h4 style="margin: 0 0 1px 0; font-size: 14px; color: white;">Travel Time (hours)</h4>
            <div style="display: flex; width: 100%; height: 8px; {gradient_css}; margin-bottom: 2px;"></div>
            <div style="display: flex; width: 100%; font-size: 14px; color: white;">{labels_html}</div>
        </div>
        """
        return legend_html


    @st.cache_data
    def load_precomputed_data():
        data = pd.read_csv(precomputed_data_path)
        # Convert travel_time to numeric (in hours), errors='coerce' will convert non-numeric values to NaN
        data['travel_time_hours'] = pd.to_timedelta(data['travel_time']).dt.total_seconds() / 3600
        return data


    precomputed_routes = load_precomputed_data()

    # Set base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct file paths
    stops_path = os.path.join(base_dir, '..', 'gtfs', 'stops.txt')
    stop_times_path = os.path.join(base_dir, '..', 'gtfs', 'stop_times.txt')

    # Load GTFS data
    @st.cache_data
    def load_gtfs_data():
        stops_df = pd.read_csv(stops_path)
        stop_times_df = pd.read_csv(stop_times_path)
        return stops_df, stop_times_df


    stops_df, stop_times_df = load_gtfs_data()

    # Calculate the number of trips servicing each stop
    trip_frequencies = stop_times_df['stop_id'].value_counts().reset_index()
    trip_frequencies.columns = ['stop_id', 'trip_count']

    # Merge the frequencies with the stops data
    stops_with_frequencies = pd.merge(stops_df, trip_frequencies, on='stop_id', how='left')
    stops_with_frequencies['trip_count'] = stops_with_frequencies['trip_count'].fillna(0)

    # Streamlit interface
    st.title("Trip and Transfer Visualization")

    # Input for city name, max travel hours, max changes, and min trip frequency
    with st.container():
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)

        with col_filter1:
            city_name = st.text_input("Enter a starting city name:", st.session_state['city_name'])
        with col_filter2:
            max_travel_hours = st.number_input("Enter the max travel hours:", min_value=1, max_value=8,
                                               value=st.session_state['max_travel_hours'])
        with col_filter3:
            max_changes = st.number_input("Enter the max number of changes:", min_value=0, max_value=3,
                                          value=st.session_state['max_changes'])
        with col_filter4:
            time_interval_label = st.selectbox("Select time interval:",
                                               list(time_interval_labels.values()),
                                               index=list(time_interval_labels.keys()).index(
                                                   st.session_state['time_interval']))
            time_interval = list(time_interval_labels.keys())[
                list(time_interval_labels.values()).index(time_interval_label)]

    # Filter precomputed data based on inputs
    def get_reachable_stops(city_name, max_travel_hours, max_changes, time_interval):
        # Filter for the specified starting city
        city_stops = stops_df[stops_df['stop_name'].str.contains(city_name, case=False, na=False)]
        city_stop_ids = city_stops['stop_id'].tolist()

        # Find trips that contain the specified city stops
        city_trip_ids = stop_times_df[stop_times_df['stop_id'].isin(city_stop_ids)]['trip_id'].unique()

        # Apply time interval filter if not "All Day"
        if time_interval != 'all_day':
            precomputed_filtered = precomputed_routes[
                (precomputed_routes['origin_city'].str.contains(city_name, case=False, na=False)) &
                (precomputed_routes['travel_time_hours'] <= max_travel_hours) &
                (precomputed_routes['transfer_count'] <= max_changes) &
                (precomputed_routes['departure_time_interval'] == time_interval)
                ]
        else:
            precomputed_filtered = precomputed_routes[
                (precomputed_routes['origin_city'].str.contains(city_name, case=False, na=False)) &
                (precomputed_routes['travel_time_hours'] <= max_travel_hours) &
                (precomputed_routes['transfer_count'] <= max_changes)
                ]

        # Ensure `arrival_time` and `travel_time` are parsed as `Timedelta` objects
        precomputed_filtered['arrival_time'] = pd.to_timedelta(precomputed_filtered['arrival_time'], errors='coerce')
        precomputed_filtered['travel_time'] = pd.to_timedelta(precomputed_filtered['travel_time'], errors='coerce')

        # Calculate departure time
        precomputed_filtered['departure_time'] = precomputed_filtered['arrival_time'] - precomputed_filtered[
            'travel_time']

        # Extract city names from stop names
        precomputed_filtered.loc[:, 'city'] = precomputed_filtered['stop_name'].str.split().str[0]

        # Sort by city and travel_time_hours, and then drop duplicates
        precomputed_filtered = precomputed_filtered.sort_values(by=['city', 'travel_time_hours']).drop_duplicates(
            subset=['city'], keep='first')

        # Check if data is found
        has_data = not precomputed_filtered.empty

        return precomputed_filtered, has_data

    # Button to trigger fetching of data
    if st.button("Find Trips"):
        reachable_stops_info, has_data = get_reachable_stops(city_name, max_travel_hours, max_changes, time_interval)
        st.session_state['reachable_stops_info'] = reachable_stops_info
        st.session_state['selected_trip'] = None
        st.session_state['city_name'] = city_name
        st.session_state['max_travel_hours'] = max_travel_hours
        st.session_state['max_changes'] = max_changes
        st.session_state['time_interval'] = time_interval
        st.session_state['has_data'] = has_data
        st.rerun()
    else:
        reachable_stops_info = st.session_state.get('reachable_stops_info', pd.DataFrame())
        has_data = st.session_state.get('has_data', True)

    # Display message if no data found
    if not has_data:
        st.warning("No trips found for the selected filters.")

    # Retrieve selected_trip_id from query params
    selected_trip_id = st.query_params.get('selected_trip_id', [None])[0]

    # Set selected_trip based on selected_trip_id from query params
    if selected_trip_id and selected_trip_id in reachable_stops_info['stop_id'].values:
        selected_trip = reachable_stops_info[reachable_stops_info['stop_id'] == selected_trip_id].iloc[0]
        st.session_state['selected_trip'] = selected_trip
    else:
        selected_trip = st.session_state.get('selected_trip', None)

    # Display the map and trip list with details box
    col1, col2, col3 = st.columns([2, 1, 1])


    def visualize_reachable_destinations(reachable_stops_info, start_coords=None, selected_trip=None):
        if reachable_stops_info.empty:
            st.warning("No stops found for the specified city.")
            return None

        stop_name_to_id = dict(zip(reachable_stops_info['stop_name'], reachable_stops_info['stop_id']))
        query_params = st.query_params
        if selected_trip is not None:
            end_coords = [selected_trip['stop_lat'], selected_trip['stop_lon']]
            center = [(start_coords[0] + end_coords[0]) / 2, (start_coords[1] + end_coords[1]) / 2]
        elif 'map_center_lat' in query_params and 'map_center_lon' in query_params:
            center = [float(query_params['map_center_lat']), float(query_params['map_center_lon'])]
        else:
            center = start_coords

        map_city = folium.Map(location=center, zoom_start=6, tiles='CartoDB positron')
        min_hours = reachable_stops_info['travel_time_hours'].min()
        max_hours = reachable_stops_info['travel_time_hours'].max()

        # Add a distinct marker for the starting city
        folium.Marker(
            location=start_coords,
            icon=folium.Icon(color='green', icon='star'),
            tooltip='Start City'
        ).add_to(map_city)

        # Add markers for directly reachable stops
        for _, row in reachable_stops_info.iterrows():
            stop_coords = [row['stop_lat'], row['stop_lon']]
            color = get_color(row['travel_time_hours'], min_hours, max_hours)
            if selected_trip is not None and row['stop_id'] == selected_trip['stop_id']:
                # Draw a gradient line between start and selected destination
                num_segments = 20
                for i in range(num_segments):
                    fraction = i / num_segments
                    segment_color = interpolate_color(get_color(min_hours, min_hours, max_hours), color, fraction)
                    intermediate_point = [
                        start_coords[0] + fraction * (stop_coords[0] - start_coords[0]),
                        start_coords[1] + fraction * (stop_coords[1] - start_coords[1])
                    ]
                    next_fraction = (i + 1) / num_segments
                    next_point = [
                        start_coords[0] + next_fraction * (stop_coords[0] - start_coords[0]),
                        start_coords[1] + next_fraction * (stop_coords[1] - start_coords[1])
                    ]
                    folium.PolyLine(
                        locations=[intermediate_point, next_point],
                        color=segment_color,
                        weight=3,
                        opacity=0.8
                    ).add_to(map_city)

                # Highlight the selected destination
                folium.CircleMarker(
                    location=stop_coords,
                    radius=10,  # Increased radius size for selected trip
                    color='darkgreen',  # Dark green highlight color for selected trip
                    weight=3,  # Outline thickness for selected trip
                    fill=True,
                    fill_color=color,
                    fill_opacity=1,  # Full opacity for selected trip
                    tooltip=row['stop_name']  # Set tooltip to stop_name
                ).add_to(map_city)
            else:
                folium.CircleMarker(
                    location=stop_coords,
                    radius=5,  # Reduced radius size
                    color='black',  # Outline color
                    weight=1,  # Outline thickness
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.6,
                    tooltip=row['stop_name']  # Set tooltip to stop_name
                ).add_to(map_city)

        plugins.Fullscreen().add_to(map_city)

        return map_city, stop_name_to_id


    with col1:
        if not reachable_stops_info.empty:
            # Generate legend HTML
            min_hours = reachable_stops_info['travel_time_hours'].min()
            max_hours = max_travel_hours  # use the input max_travel_hours to limit the legend
            legend_html = get_legend_html(min_hours, max_hours, width=695)

            # Display legend
            st.markdown(legend_html, unsafe_allow_html=True)

            # Determine the start coordinates from the city name
            start_coords = stops_df[stops_df['stop_name'].str.contains(city_name, case=False, na=False)]
            if not start_coords.empty:
                start_coords = [start_coords.iloc[0]['stop_lat'], start_coords.iloc[0]['stop_lon']]

            selected_trip = st.session_state.get('selected_trip', None)
            map_city, stop_name_to_id = visualize_reachable_destinations(reachable_stops_info, start_coords=start_coords,
                                                        selected_trip=selected_trip)
            if map_city:
                st_data = st_folium(map_city, width=695, height=500, returned_objects=["last_object_clicked", "last_object_clicked_tooltip"])

                # Capture click event from the map
                if st_data and "last_object_clicked_tooltip" in st_data:
                    clicked_stop_name = st_data["last_object_clicked_tooltip"]
                    clicked_stop_id = stop_name_to_id.get(clicked_stop_name, None)
                    if clicked_stop_id and (st.session_state.get('selected_trip_id') != clicked_stop_id):
                        if clicked_stop_id in reachable_stops_info['stop_id'].values:
                            selected_trip = reachable_stops_info[reachable_stops_info['stop_id'] == clicked_stop_id].iloc[0]
                            st.session_state['selected_trip'] = selected_trip
                            st.session_state['selected_trip_id'] = clicked_stop_id
                            # Set the scroll position in the session state
                            st.session_state['scroll_position'] = st.session_state.get('scroll_position', 0)
                            st.query_params.update({
                                'map_center_lat': selected_trip['stop_lat'],
                                'map_center_lon': selected_trip['stop_lon'],
                                'scroll_position': st.session_state['scroll_position'],
                                'selected_trip_id': clicked_stop_id  # Add selected_trip_id to query params
                            })
                            st.rerun()

    with col2:
        if not reachable_stops_info.empty:
            st.write("## List of Trips")

            # Define the trip list
            trip_list = reachable_stops_info[['stop_name', 'travel_time']].reset_index(drop=True)

            # Search input
            search_term = st.text_input("Search trips", "")

            # Filter the trip list based on the search term
            if search_term:
                filtered_trip_list = trip_list[trip_list['stop_name'].str.contains(search_term, case=False)]
            else:
                filtered_trip_list = trip_list

            # Create a scrollable container for the list of trips
            with st.container(height=430):

                # Capture click event from the list
                def display_trip_details(idx):
                    selected_trip = reachable_stops_info.iloc[idx]
                    st.session_state['selected_trip'] = selected_trip
                    st.session_state['selected_trip_id'] = selected_trip['stop_id']
                    st.session_state['map_center'] = [selected_trip['stop_lat'], selected_trip['stop_lon']]
                    # Set the scroll position in the session state
                    st.session_state['scroll_position'] = st.query_params.get('scroll_position', 0)
                    st.query_params.update({
                        'map_center_lat': selected_trip['stop_lat'],
                        'map_center_lon': selected_trip['stop_lon'],
                        'scroll_position': st.session_state['scroll_position']
                    })
                    st.rerun()  # Force rerun to update map immediately


                for idx, row in filtered_trip_list.iterrows():
                    if st.button(row['stop_name'], key=f"{row['stop_name']}_{idx}"):
                        display_trip_details(idx)

    with col3:
        # Display details box
        if 'selected_trip' in st.session_state and st.session_state['selected_trip'] is not None:
            selected_trip = st.session_state['selected_trip']
            st.write("### Selected Trip Details")
            st.markdown(f"""
                **Stop Name:** {selected_trip['stop_name']}  
                **Departure Time:** {selected_trip['departure_time']}  
                **Arrival Time:** {selected_trip['arrival_time']}  
                **Travel Time:** {selected_trip['travel_time']}  
                **Number of Changes:** {selected_trip['transfer_count']}  
            """)
