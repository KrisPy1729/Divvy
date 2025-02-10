import requests
import streamlit as st

def get_data(url, retries=4):
    """ This function gets json response of a given url using requests and generate appropriate error responses if necessary """
    
    for _ in range(retries):
        # tries to get a response 'retries' times with a delay of 'delay' seconds and then displays respecitve errors, if necessary
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                # displays received response codes from server side 
                st.error(f"Error fetching the feed: Error {response.status_code}")
                
        except requests.exception.RequestException as request_error:
            # if the request didn't go through to the server at all, then displays respective errors
            st.error(f"Request failed: {request_error}")
           
        
def get_data_lang(feed_data, l="en"):
    """ This function gets the json response and required language as parameters and returns the json of that specific language key """
    
    if 'data' in feed_data and l in feed_data['data']:
        # checks if there's a key called data and then selects the part of json under desired language
        return feed_data['data'][l]
    else:
        return None
    

def feeds_extractor(feeds):
    """ This function gets the list called feeds and extracts the name, and json response to the respective url as key-value pairs into a dictionary and returns it """
    
    project_json = {}
    
    for feed in feeds:
        # loops over the name, url value pair inside feeds
        feed_name = feed['name']
        link = feed['url']
        
        # gets json responses for those specific urls
        data = get_data(link)
        
        # checks if these json responses have data and then extracts the part inside 'data' key of those json responses
        if "data" in data:
            project_json[feed_name] = data['data']
            
        else:
            st.warning(f"No 'data' field found for {feed_name}")
    return project_json


def st_lang_buttons():
    """ This function sets English as the default language, displays 3 buttons for EN, FR, and ES in streamlit, and extracts the respective part of json, and returns this language selection to main() """
    
    # default language en
    lang = "en"
    
    # setting up 3 columns/containers in streamlit to display the buttons
    col1, col2, col3 = st.columns(3)
    
    # with helps in declaring which button goes in which container/column and set the user-desired language as the value of the return variable
    with col1:
        if st.button("🇺🇸"):
            lang = "en"
    with col2:
        if st.button("🇫🇷"):
            lang = "fr"
    with col3:
        if st.button("🇪🇸"):
            lang = "es"
    return lang
