import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from divvy_streamlit_functions import *

# Caching the data fetching function
@st.cache_data(show_spinner=False)
def get_divvy_data(url):
    """ Fetching data using the function containing the requests library """
    return get_data(url)

# Caching the dataframe creation and data processing
@st.cache_data(show_spinner=False)
def create_station_dashboard(divvy_data, lang):
    """Process and create the station dashboard data."""
    # Display title
    st.title("Divvy Bike Dashboard")

    if divvy_data is None:
        return None
    
    divvy_data_lang = get_data_lang(divvy_data, lang)
    
    if divvy_data_lang:
        divvy_feeds_json = feeds_extractor(divvy_data_lang['feeds'])
    else:
        st.warning("The feed doesn't contain data in any defined languages")
        return None
    
    # Normalizing and flattening the JSONs into dataframes
    station_information_df = pd.json_normalize(divvy_feeds_json['station_information']['stations'])
    station_status_df = pd.json_normalize(divvy_feeds_json['station_status']['stations'], record_path='vehicle_types_available', 
                                          meta=['num_docks_available', 'num_bikes_available', 'is_renting', 'is_installed', 
                                                'num_docks_disabled', 'num_scooters_available', 'num_bikes_disabled', 'last_reported', 
                                                'is_returning', 'num_ebikes_available', 'station_id', 'num_scooters_unavailable'], errors='ignore')
    station_status_df['vehicle_type_id'] = station_status_df['vehicle_type_id'].astype(int)
    
    free_bike_status_df = pd.json_normalize(divvy_feeds_json['free_bike_status']['bikes'])
    vehicle_types_df = pd.json_normalize(divvy_feeds_json['vehicle_types']['vehicle_types'])
    vehicle_types_df['vehicle_type_id'] = vehicle_types_df['vehicle_type_id'].astype(int)
    
    pricing_plans_df = pd.json_normalize(divvy_feeds_json['system_pricing_plans']['plans'], record_path='per_min_pricing', 
                                         meta=['price', 'currency', 'description', 'name', 'plan_id', 'is_taxable'], errors='ignore')
    
    # Merging and processing the vehicle data
    available_vehicle_count = station_status_df[['station_id', 'vehicle_type_id', 'count']]
    vehicles_df = pd.merge(available_vehicle_count, vehicle_types_df, on='vehicle_type_id', how='left')
    
    vehicles_df_conditions = [(vehicles_df['vehicle_type_id'] == 1), (vehicles_df['vehicle_type_id'] == 2), (vehicles_df['vehicle_type_id'] == 3)]
    vehicles_df_choices = ["Bike", "E-Bike", "E-Scooter"]
    vehicles_df['Category'] = np.select(vehicles_df_conditions, vehicles_df_choices, default="Other")
    vehicles_df = vehicles_df[['station_id', 'Category', 'count']]
    
    vehicles_df_pivoted = pd.pivot_table(vehicles_df, index='station_id', columns=['Category'], values='count', aggfunc='sum', fill_value=0)
    vehicles_df_pivoted.columns = [f'available_{col}' for col in vehicles_df_pivoted.columns]
    vehicles_df_pivoted.reset_index(inplace=True)
    vehicle_status = vehicles_df_pivoted
    
    # Merging and cleaning the dataframes (just like before)
    station_status_df.drop(columns=['vehicle_type_id', 'count'], inplace=True)
    station_status_df.drop_duplicates(subset=['station_id'], inplace=True)
    station_status = pd.merge(station_status_df, vehicle_status, on='station_id', how='left')
    
    station_dashboard_df = pd.merge(station_status, station_information_df, on='station_id', how='left')
    station_dashboard_df = station_dashboard_df[['station_id', 'name', 'short_name', 'lat', 'lon', 'capacity', 'region_id', 'address', 
                                                 'is_installed', 'is_returning', 'is_renting', 'num_docks_available', 'available_Bike', 
                                                 'available_E-Bike',  'available_E-Scooter', 'last_reported']]
    station_dashboard_df['last_reported'] = pd.to_datetime(station_dashboard_df['last_reported'], unit='s')

    return station_dashboard_df

# Caching the map creation process
@st.cache_data(show_spinner=False)
def create_map(station_dashboard_df):
    """Create the folium map."""
    map = folium.Map(location=[41.881832, -87.623177], zoom_start=10)
    
    mc = MarkerCluster().add_to(map)

    for index, row in station_dashboard_df.iterrows():
        tooltip_text = "<br>".join([ f"📌<b>{row['name']}</b>", 
                                    f"Available empty docks: {row['num_docks_available']} 🅿️", 
                                    f"Available Bikes: {row['available_Bike']} 🚲", 
                                    f"Available <b><span style='color: gold;'>E-Bikes</span></b>: {row['available_E-Bike']} 🚲⚡",
                                    f"Available <b><span style='color: gold;'>E-Scooters</span></b>: {row['available_E-Scooter']} 🛴⚡"
                                   ])
        if (row['is_installed'] == 1) & (row['is_renting'] == 1):
            icon_color = 'green'
            icon_type = 'ok-sign'
        elif (row['is_installed'] == 0) | (row['is_renting'] == 0):
            icon_color = 'red'
            icon_type = 'remove-sign'

        folium.Marker(
            location=[row['lat'], row['lon']], 
            tooltip=tooltip_text,
            icon=folium.Icon(color=icon_color, icon=icon_type, popup=tooltip_text)
        ).add_to(mc)

    folium.LayerControl().add_to(map)
    # Add the marker cluster to the map
    map.add_child(mc)
    
    return map

def main():
    """Main function for the dashboard."""
        
    # Fetching the data from the URL
    divvy_gbfs_feed = 'https://gbfs.divvybikes.com/gbfs/2.3/gbfs.json'
    divvy_data = get_divvy_data(divvy_gbfs_feed)
    
    # Materialize user clickable language buttons in streamlit, sets the default language if the user is a lazy English speaking monolingual
    lang = st_lang_buttons()
    
    # Creating stations dashboard
    station_dashboard_df = create_station_dashboard(divvy_data, lang)

    if station_dashboard_df is None:
        st.error("Failed to load data!")
        return
    
    # Creating the map (cached)
    map = create_map(station_dashboard_df)

    # Displaying the map using streamlit_folium
    st_folium(map, height=500, width=700, returned_objects=[])

if __name__ == "__main__":
    main()
