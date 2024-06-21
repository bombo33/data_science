import pandas as pd
import numpy as np
import streamlit as st
import folium
from streamlit_folium import folium_static
from shapely.geometry import Polygon, Point
import geopandas as gpd
import h3
import matplotlib.pyplot as plt

# Load GTFS data
stops_df = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/stops.txt')
stop_times_df = pd.read_csv('/home/anatol/Documents/2023_24_2/DS/gtfs_generic_eu/stop_times.txt')

# Load region boundaries (example: NUTS regions in Europe, available from Eurostat)
regions_gdf = gpd.read_file('/home/anatol/Documents/2023_24_2/DS/FlixBusProject/cleaning/NUTS_RG_01M_2021_4326.shp/NUTS_RG_01M_2021_4326.shp')

# Calculate the number of trips servicing each stop
trip_frequencies = stop_times_df['stop_id'].value_counts().reset_index()
trip_frequencies.columns = ['stop_id', 'trip_count']

# Merge the trip frequencies with the stops data
stops_with_frequencies = pd.merge(stops_df, trip_frequencies, on='stop_id', how='left')
stops_with_frequencies['trip_count'] = stops_with_frequencies['trip_count'].fillna(0)

# Convert stops_with_frequencies to GeoDataFrame
stops_gdf = gpd.GeoDataFrame(
    stops_with_frequencies, geometry=gpd.points_from_xy(stops_with_frequencies.stop_lon, stops_with_frequencies.stop_lat)
)

# Perform spatial join to aggregate frequencies by region
regions_with_frequencies = gpd.sjoin(regions_gdf, stops_gdf, how='left', op='contains')
region_freq = regions_with_frequencies.groupby('index_left')['trip_count'].sum().reset_index()
regions_gdf = regions_gdf.merge(region_freq, left_index=True, right_on='index_left', how='left')
regions_gdf['trip_count'] = regions_gdf['trip_count'].fillna(0)

# Streamlit UI
st.title('FlixBus Service Heatmap')
st.write("This heatmap shows how well different areas are serviced by FlixBus, based on the number of routes and their frequencies.")

# Create a folium map
m = folium.Map(location=[stops_with_frequencies['stop_lat'].mean(), stops_with_frequencies['stop_lon'].mean()], zoom_start=6)

# Function to add regions to the map
def add_regions_to_map(map_obj, regions_gdf):
    max_freq = regions_gdf['trip_count'].max()
    for _, row in regions_gdf.iterrows():
        if pd.notna(row['trip_count']):
            color = plt.cm.Reds(row['trip_count'] / max_freq)
            color_rgba = f'rgba({int(color[0] * 255)}, {int(color[1] * 255)}, {int(color[2] * 255)}, 0.6)'
            folium.GeoJson(
                row['geometry'].__geo_interface__,
                style_function=lambda feature, color_rgba=color_rgba: {
                    'fillColor': color_rgba,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.6
                }
            ).add_to(map_obj)

# Add regions to the map
add_regions_to_map(m, regions_gdf)

# Add a legend to the map
legend_html = '''
<div style="
    position: fixed;
    bottom: 50px;
    left: 50px;
    width: 150px;
    height: 150px;
    background-color: white;
    border:2px solid grey;
    z-index:9999;
    font-size:14px;
    ">
    <b>&nbsp;Heatmap Legend</b><br>
    &nbsp;<i style="background: rgba(255, 0, 0, 0.6); width: 10px; height: 10px; display: inline-block;"></i>&nbsp;High<br>
    &nbsp;<i style="background: rgba(255, 165, 0, 0.6); width: 10px; height: 10px; display: inline-block;"></i>&nbsp;Medium<br>
    &nbsp;<i style="background: rgba(255, 255, 0, 0.6); width: 10px; height: 10px; display: inline-block;"></i>&nbsp;Low<br>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Display the map in Streamlit
folium_static(m)

# Show the dataframe with stops and their trip frequencies
st.subheader('Stops with Trip Frequencies')
st.dataframe(stops_with_frequencies[['stop_name', 'trip_count']].sort_values(by='trip_count', ascending=False))



