### Methodology and Rationale for FlixBus Service Heatmap

#### Data Selection and Sources

To visualize the FlixBus service coverage across Europe, we used two primary datasets:

1. **GTFS (General Transit Feed Specification) Data**:
    - **stops.txt**: This file contains information about all bus stops, including their geographic coordinates. It is essential for mapping the physical locations of the stops.
    - **stop_times.txt**: This file provides the arrival and departure times for each stop on each trip. It is crucial for calculating the frequency of service at each stop.

2. **NUTS Regions Shapefile**:
    - **NUTS_RG_01M_2021_4326.shp**: This shapefile contains the geographic boundaries of the NUTS regions. NUTS (Nomenclature of Territorial Units for Statistics) is a geocode standard for referencing the subdivisions of countries for statistical purposes. The NUTS shapefile is necessary for spatially aggregating the service data.

#### Rationale for Using Two NUTS Levels

The choice to use NUTS level 2 for Germany and NUTS level 3 for other countries is driven by the following considerations:

- **Regional Disparities**: Germany, being a larger country with more granular administrative divisions, benefits from using NUTS level 2, which provides a more aggregated view suitable for high-level analysis. This level offers a balanced view of service coverage without getting lost in overly detailed subdivisions.
- **Comparative Analysis**: For other European countries, NUTS level 3 is used to maintain a consistent and detailed view of service coverage across smaller regions. This allows for a more granular analysis of service distribution, which is necessary for identifying local disparities in less densely populated or smaller countries.

#### Methodology

1. **Data Loading and Preparation**:
    - **Stops and Stop Times**: The stops and stop times data were loaded from the GTFS dataset. The stop times data were used to calculate the frequency of trips servicing each stop.
    - **NUTS Regions**: The NUTS shapefile was loaded and transformed to ensure the Coordinate Reference System (CRS) matched the stops data.

2. **Spatial Aggregation**:
    - **Merging Trip Frequencies**: The trip frequencies were calculated by counting the number of trips per stop from the stop times data. This frequency data was then merged with the stops data.
    - **GeoDataFrame Conversion**: The stops data, now containing trip frequencies, was converted into a GeoDataFrame for spatial operations.
    - **Spatial Join**: A spatial join was performed between the NUTS regions and the stops GeoDataFrame to aggregate the trip frequencies by region. This process assigns each stop to its corresponding NUTS region and sums the trip frequencies within each region.

3. **Visualization**:
    - **Heatmap Creation**: The aggregated data were visualized using Folium to create an interactive heatmap. Each region's color intensity on the map represents the frequency of FlixBus services.
    - **Interactivity**: Tooltips were added to provide detailed information on the region name and the number of trips when hovered over.

#### Results and Interpretation

The resulting heatmap highlights the distribution of FlixBus services across Europe. Regions with higher service frequencies are easily identifiable, providing insights into regional service disparities. The interactive nature of the map allows for detailed exploration of specific areas, making it a valuable tool for transportation planning and analysis.