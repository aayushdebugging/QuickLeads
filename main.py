import streamlit as st
import requests
import csv
import time
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define your Google API Key
API_KEY = os.getenv('GOOGLE_API_KEY')  # Fetching API key from .env file

# Function to search for places based on a query or coordinates
def search_places(query=None, latitude=None, longitude=None, radius=None):
    endpoint_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    places = []

    # Define parameters based on user input
    params = {
        'key': API_KEY,
    }

    # Use query-based search if query is provided
    if query:
        params['query'] = query
    # If latitude and longitude are provided, use those with optional radius
    if latitude and longitude:
        endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params['location'] = f"{latitude},{longitude}"
        if radius:  # Only include radius if coordinates are provided
            params['radius'] = radius  # Radius in meters

    while True:
        try:
            response = requests.get(endpoint_url, params=params)
            response.raise_for_status()
            places_data = response.json()

            if 'results' in places_data:
                places.extend(places_data['results'])

            if 'next_page_token' in places_data:
                time.sleep(2)
                params['pagetoken'] = places_data['next_page_token']
            else:
                break
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching data: {e}")
            break

    return places

# Function to get full place details
def get_full_place_details(place_id):
    endpoint_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {'place_id': place_id, 'key': API_KEY}

    try:
        response = requests.get(endpoint_url, params=params)
        response.raise_for_status()
        place_details = response.json()

        if 'result' in place_details:
            return place_details['result']
        else:
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching place details: {e}")
        return {}

# Function to save places information to a CSV file and return its DataFrame
def save_places_to_csv(places):
    keys = [
        'name', 'address', 'phone', 'website', 'rating', 'user_ratings_total',
        'place_id', 'opening_hours', 'business_status', 'price_level', 'types'
    ]

    data = []
    for place in places:
        data.append({
            'name': place.get('name', 'N/A'),
            'address': place.get('formatted_address', 'N/A'),
            'phone': place.get('formatted_phone_number', 'N/A'),
            'website': place.get('website', 'N/A'),
            'rating': place.get('rating', 'N/A'),
            'user_ratings_total': place.get('user_ratings_total', 'N/A'),
            'place_id': place.get('place_id', 'N/A'),
            'opening_hours': place.get('opening_hours', 'N/A'),
            'business_status': place.get('business_status', 'N/A'),
            'price_level': place.get('price_level', 'N/A'),
            'types': place.get('types', 'N/A')
        })
    
    df = pd.DataFrame(data)
    return df

# Function to merge full place details with initial search results
def merge_full_place_details(places):
    for place in places:
        full_details = get_full_place_details(place['place_id'])
        if full_details:
            place.update(full_details)
    return places

# Streamlit UI
st.title("Flexible Google Places Information Extractor")

# Collecting user input for text-based or location-based search
query = st.text_input("Enter the type of place and location (e.g., real estate in Dubai or restaurants in New York):")
latitude = st.text_input("Enter latitude [optional]:")
longitude = st.text_input("Enter longitude [optional]:")
radius = st.number_input("Enter radius in meters [optional]:", min_value=1, step=1)

# Validate latitude and longitude inputs if provided
try:
    latitude = float(latitude) if latitude else None
    longitude = float(longitude) if longitude else None
except ValueError:
    st.error("Latitude and longitude must be numbers.")
    latitude, longitude = None, None

if st.button("Fetch Places"):
    if query or (latitude and longitude):
        st.info(f"Fetching places with given criteria...")

        # Fetch places based on the input criteria
        places = search_places(query=query, latitude=latitude, longitude=longitude, radius=radius if latitude and longitude else None)

        if places:
            st.success(f"Found {len(places)} places.")
            places_with_details = merge_full_place_details(places)
            df = save_places_to_csv(places_with_details)
            
            # Display download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="places_data.csv",
                mime='text/csv'
            )
        else:
            st.warning("No places found with the specified criteria.")
    else:
        st.warning("Please enter either a query or latitude and longitude.")
