import streamlit as st
import pandas as pd
from divvy_streamlit_functions import *

def main():
    """ Main guy DUH! """
    
    divvy_gbfs_feed = 'https://gbfs.divvybikes.com/gbfs/2.3/gbfs.json'
    
    # let's get the json response from the url
    divvy_data = get_data(divvy_gbfs_feed)
    
    # Title of the dashboard
    st.title("Divvy BikeShare") 
    
    # Generates error response if no data loaded either due to server side error or any type of error in connecting to server
    if divvy_data is None:
        st.error("Failed to load data from the API")
        return
    
    # Materialises user clickable language buttons in streamlit, sets the default language if the user is a lazy English speaking monolingual
    lang = st_lang_buttons()
    
    
    # Gets that language specific part of the json response
    divvy_data_lang = get_data_lang(divvy_data, lang)
    
    # If the language specific data exists then sends it to extractor to get name, url pairs inside the json, then further get json responses from those urls into a dictionary
    if divvy_data_lang:
        divvy_feeds_json = feeds_extractor(divvy_data_lang['feeds'])
    else:
        # Oh well, the url has feeds only in some exotic language unknown to Americans
        st.warning("The feed doesn't contain data in any defined languages")
        return
    
    # Passes station_information to a dataframe using json_normalize
    station_information_df = pd.json_normalize(divvy_feeds_json['station_information']['stations'])
    # Passes station_status to a dataframe using json_normalize, the array has a list of dictionaries vehicle_types_available, so using record_path and meta to flatten it.
    station_status_df = pd.json_normalize(divvy_feeds_json['station_status']['stations'], record_path='vehicle_types_available', 
                                          meta=['num_docks_available', 'num_bikes_available', 'is_renting', 'is_installed', 
                                                'num_docks_disabled', 'num_scooters_available', 'num_bikes_disabled', 'last_reported', 
                                                'is_returning', 'num_ebikes_available', 'station_id', 'num_scooters_unavailable'], errors='ignore')
    
    # Passes free_bike_status to a dataframe using json_normalize
    free_bike_status_df = pd.json_normalize(divvy_feeds_json['free_bike_status']['bikes'])
    
    # using st.write to write the tables to the dashboard to verify
    st.write(station_information_df.head())
    st.write(station_status_df.head())
    st.write(free_bike_status_df.head())

if __name__ == "__main__":
    # Will help later in functional testing.... or so I think
    main()
        
    