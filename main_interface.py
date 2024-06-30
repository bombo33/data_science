import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="FlixVis",
    page_icon=":bus:",
    layout="wide",
)

from transfers.destinations_interface import destinations_interface_main
from heatmap.heatmap import heatmap_main

# Create a sidebar for page selection
page = st.sidebar.selectbox("Select a page", ["Destinations Interface", "Heatmap"])

# Call the respective function based on the selected page
if page == "Destinations Interface":
    destinations_interface_main()
elif page == "Heatmap":
    heatmap_main()