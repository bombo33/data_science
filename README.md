# Installing dependecies

Before running the project, ensure all necessary Python packages are installed. You can do this by opening a terminal, moving to the projects folder where the ***requirements.txt*** file is located and the running:

```bash
pip install -r requirements.txt
```

# How to start the interface

Right now all of the required files to run the interface are in this repository, so there is no need to do any extra steps before.

1. Open up a terminal

2. Move to the folder which contains the projects ***main_interface.py*** file

3. In the terminal run the following command:
   
   ```bash
   streamlit run main_interface.py
   ```

# To run the precomputing script:

We need to do some extra steps for that before running.

1. We ned to run the ***remove_multiple_stops_from_cities.py*** which can be found inside the transfers folder

2. After this step we need to run the ***remove_small_cities.py*** which is also in the transfers folder

3. After running this we get the ***cleaned_filtered_stops.txt*** in the gtfs folder

4. In the gtfs folder we can find the ***precomputing.ipynb***, and we can run this, and this gives back the ***precomputed_routes_no_missing_values.csv***

5. We need to rename this file to: ***precomputed_routes_adjusted_test.csv***

6. After renaming we can run the interface according to the steps written in the first part


