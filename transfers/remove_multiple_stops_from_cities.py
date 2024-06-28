import pandas as pd
import os
import re

# Set base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Construct file paths
stops_path = os.path.join(base_dir, '..', 'gtfs', 'stops.txt')
stop_times_path = os.path.join(base_dir, '..', 'gtfs', 'stop_times.txt')

# Load GTFS data
stops_df = pd.read_csv(stops_path)
stop_times_df = pd.read_csv(stop_times_path)
stops_df = stops_df.sort_values(by=['stop_name'])

# Calculate the number of trips servicing each stop
trip_frequencies = stop_times_df['stop_id'].value_counts().reset_index()
trip_frequencies.columns = ['stop_id', 'trip_count']

# Merge trip frequencies with stops data
stops_with_frequencies = pd.merge(stops_df, trip_frequencies, on='stop_id', how='left')
stops_with_frequencies['trip_count'] = stops_with_frequencies['trip_count'].fillna(0)


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


# Apply the function to extract city names
stops_with_frequencies['city_name'] = stops_with_frequencies['stop_name'].apply(extract_city_name)


# Function to find the primary stop in each city
def find_primary_stops(stops_df):
    primary_stops = []
    i = 0
    while i < len(stops_df):
        current_city = stops_df.iloc[i]['city_name']
        max_trip_count = stops_df.iloc[i]['trip_count']
        primary_stop = stops_df.iloc[i]
        j = i + 1
        while j < len(stops_df) and stops_df.iloc[j]['city_name'].startswith(current_city):
            if stops_df.iloc[j]['trip_count'] > max_trip_count:
                max_trip_count = stops_df.iloc[j]['trip_count']
                primary_stop = stops_df.iloc[j]
            j += 1
        primary_stops.append(primary_stop)
        i = j
    return pd.DataFrame(primary_stops)


# Find the primary stops
primary_stops_df = find_primary_stops(stops_with_frequencies)

# Include only the original columns
original_columns = stops_df.columns
cleaned_primary_stops_df = primary_stops_df[original_columns]

# Save the cleaned data to a new file
cleaned_stops_path = os.path.join(base_dir, '..', 'gtfs',  'cleaned_stops.txt')
cleaned_primary_stops_df.to_csv(cleaned_stops_path, index=False)

print(f"Cleaned stops data saved to {cleaned_stops_path}")
