import os
import pandas as pd
import numpy as np
import streamlit as st
import folium
from streamlit_folium import folium_static
from shapely.geometry import Polygon, Point
import geopandas as gpd
import matplotlib.pyplot as plt
from branca.colormap import linear, LinearColormap, StepColormap

# Set base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Construct file paths
stops_path = os.path.join(base_dir, '..', 'gtfs', 'stops.txt')
stop_times_path = os.path.join(base_dir, '..', 'gtfs', 'stop_times.txt')
regions_path = os.path.join(base_dir, 'NUTS_RG_01M_2021_4326.shp', 'NUTS_RG_01M_2021_4326.shp')

# Load GTFS data
stops_df = pd.read_csv(stops_path)
stop_times_df = pd.read_csv(stop_times_path)

# Calculate the number of trips servicing each stop
trip_frequencies = stop_times_df['stop_id'].value_counts().reset_index()
trip_frequencies.columns = ['stop_id', 'trip_count']

# Load region boundaries (NUTS regions in Europe, available from Eurostat)
regions_gdf = gpd.read_file(regions_path)

# Ensure the CRS is the same
regions_gdf = regions_gdf.to_crs(epsg=4326)

# Filter NUTS level 2 regions for Germany and level 3 regions for other countries
regions_germany = regions_gdf[(regions_gdf['LEVL_CODE'] == 2) & (regions_gdf['CNTR_CODE'] == 'DE')]
regions_others = regions_gdf[(regions_gdf['LEVL_CODE'] == 3) & (regions_gdf['CNTR_CODE'] != 'DE')]

# Combine the filtered regions
regions_gdf_combined = pd.concat([regions_germany, regions_others])

# Debug print to check the NUTS ID and level code
print(regions_gdf_combined[['NUTS_ID', 'LEVL_CODE', 'CNTR_CODE']].head(10))

stops_with_frequencies = pd.merge(stops_df, trip_frequencies, on='stop_id', how='left')
stops_with_frequencies['trip_count'] = stops_with_frequencies['trip_count'].fillna(0)

# Convert stops_with_frequencies to GeoDataFrame with the same CRS
stops_gdf = gpd.GeoDataFrame(
    stops_with_frequencies,
    geometry=gpd.points_from_xy(stops_with_frequencies.stop_lon, stops_with_frequencies.stop_lat),
    crs="EPSG:4326"
)

# Perform spatial join to aggregate frequencies by region
regions_with_frequencies = gpd.sjoin(regions_gdf_combined, stops_gdf, how='left', predicate='contains')

# Ensure we use the correct column for the join key
regions_with_frequencies = regions_with_frequencies.reset_index()
region_freq = regions_with_frequencies.groupby('index')['trip_count'].sum().reset_index()
regions_gdf_combined = regions_gdf_combined.reset_index().merge(region_freq, left_on='index', right_on='index', how='left')
regions_gdf_combined['trip_count'] = regions_gdf_combined['trip_count'].fillna(0)

# Filter out regions with zero trips
regions_gdf_filtered = regions_gdf_combined[regions_gdf_combined['trip_count'] > 0]

# Use NAME_LATN for region names
regions_gdf_filtered = regions_gdf_filtered.rename(columns={'NAME_LATN': 'Region', 'trip_count': 'Trips'})

# Convert GeoDataFrame to GeoJSON and add required properties
regions_geojson = regions_gdf_filtered.to_json()

# Function to add regions to the map
def add_regions_to_map(map_obj, geojson_data, colormap):
    folium.GeoJson(
        geojson_data,
        style_function=lambda feature: {
            'fillColor': colormap(feature['properties']['Trips']),
            'color': 'black',  # Thin border color
            'weight': 0.5,  # Thin border width
            'fillOpacity': 0.8
        },
        tooltip=folium.GeoJsonTooltip(fields=['Region', 'Trips'], aliases=['Region:', 'Trips:'])
    ).add_to(map_obj)

# Define a stepped colormap with distinct colors based on trip counts
min_trip_count = regions_gdf_filtered['Trips'].min()
max_trip_count = regions_gdf_filtered['Trips'].max()

print(f"Min trip count: {min_trip_count}, Max trip count: {max_trip_count}")

# Adjust color bins to reflect actual trip count range, including min_trip_count
color_bins = [min_trip_count, 100, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, max_trip_count]
colors = ['#ffffcc', '#c2e699', '#78c679', '#31a354', '#006837', '#004529', '#003000', '#002000', '#001000', '#000800', '#000400', '#000200']

# Ensure the number of colors matches the number of bins - 1
if len(colors) != len(color_bins) - 1:
    raise ValueError("The number of colors must be equal to the number of bins - 1")

colormap = StepColormap(colors, vmin=min_trip_count, vmax=max_trip_count, index=color_bins, caption='Trip Frequencies')

# Calculate the center of the map based on stops
center_lat = stops_with_frequencies['stop_lat'].mean()
center_lon = stops_with_frequencies['stop_lon'].mean()

# Streamlit UI
st.set_page_config(layout="wide")
st.title('FlixBus Service Heatmap')
st.write("This heatmap shows how well different areas are serviced by FlixBus, based on the number of routes and their frequencies.")

# Center map on Streamlit interface
st.write('<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)

# Create a folium map
m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

# Add regions to the map
add_regions_to_map(m, regions_geojson, colormap)

# Add the color bar to the map
colormap.add_to(m)

# Display the map in Streamlit with larger dimensions
folium_static(m, width=1200, height=800)

