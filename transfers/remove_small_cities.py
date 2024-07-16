import pandas as pd
import os
import re

# Set base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Construct file paths
stops_path = os.path.join(base_dir, '..', 'gtfs', 'cleaned_stops.txt')
population_data_path = '../gtfs/geonames-all-cities-with-a-population-1000.csv'

# Load cleaned primary stops data
stops_df = pd.read_csv(stops_path)

# Load the population dataset with semicolon delimiter and specify dtypes
population_dtypes = {
    'Geoname ID': 'int64',
    'Name': 'str',
    'ASCII Name': 'str',
    'Alternate Names': 'str',
    'Feature Class': 'str',
    'Feature Code': 'str',
    'Country Code': 'str',
    'Country name EN': 'str',
    'Country Code 2': 'str',
    'Admin1 Code': 'str',
    'Admin2 Code': 'str',
    'Admin3 Code': 'str',
    'Admin4 Code': 'str',
    'Population': 'int64',
    'Elevation': 'str',
    'DIgital Elevation Model': 'str',
    'Timezone': 'str',
    'Modification date': 'str',
    'LABEL EN': 'str',
    'Coordinates': 'str'
}

population_df = pd.read_csv(population_data_path, delimiter=';', dtype=population_dtypes, low_memory=False)

# Filter cities with population >= 100,000
large_cities_df = population_df[population_df['Population'] >= 50000]

# Define the function to extract city names
def extract_city_name(stop_name):
    match = re.match(r'^[^\(,]*', stop_name)
    city_name = match.group(0).strip() if match else stop_name

    non_city_words = [
        'Bus Station', 'Airport', 'Service Area', 'FlixBus stop', 'Central Station',
        'Station', 'Eastbound', 'Westbound', 'East', 'West', 'North', 'South',
        'Business', 'Park', 'Plaza', 'Square', 'Circle', 'Center', 'Centre',
        'Stop', 'St.', 'Street', 'Rd.', 'Road', 'Ave.', 'Avenue', 'Dr.', 'Drive'
    ]

    for word in non_city_words:
        city_name = re.sub(rf'\b{word}\b', '', city_name, flags=re.IGNORECASE).strip()

    city_name_parts = city_name.split()
    significant_parts = []
    for part in city_name_parts:
        if part and part.istitle():
            significant_parts.append(part)
        else:
            break

    city_name = ' '.join(significant_parts) if significant_parts else city_name_parts[0]

    return city_name

# Define the function to find the best matching city name
def find_matching_city_name(city_name, large_city_names):
    if city_name in large_city_names:
        return city_name
    else:
        city_name_parts = city_name.split()
        for i in range(len(city_name_parts), 0, -1):
            potential_city_name = ' '.join(city_name_parts[:i])
            if potential_city_name in large_city_names:
                return potential_city_name
    return None

# Apply the function to extract city names
stops_df['city_name'] = stops_df['stop_name'].apply(extract_city_name)

# Get the list of large city names
large_city_names = large_cities_df['Name'].str.strip().unique()

# Apply the function to find matching city names
stops_df['matched_city_name'] = stops_df['city_name'].apply(lambda x: find_matching_city_name(x, large_city_names))

# Filter stops to include only those in large cities
filtered_stops_df = stops_df[stops_df['matched_city_name'].notna()]

# Include only the original columns
original_columns = stops_df.columns.drop(['city_name', 'matched_city_name'])
cleaned_filtered_stops_df = filtered_stops_df[original_columns]

# Save the filtered data to a new file
cleaned_stops_path = os.path.join(base_dir, '..', 'gtfs', 'cleaned_filtered_stops.txt')
cleaned_filtered_stops_df.to_csv(cleaned_stops_path, index=False)

print(f"Filtered stops data saved to {cleaned_stops_path}")
