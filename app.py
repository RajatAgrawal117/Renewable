import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import geocoder
from plyer import notification

# Page Configuration (This should be the first Streamlit command)
st.set_page_config(page_title="EV Charging Station Finder", layout="wide")

# Custom CSS to style the app
st.markdown("""
    <style>
        .title {
            font-family: 'Helvetica Neue', sans-serif;
            font-size: 36px;
            color: #4C9EFF;
            font-weight: bold;
            text-align: center;
        }
        .header {
            font-family: 'Roboto', sans-serif;
            font-size: 28px;
            color: #333;
            font-weight: 600;
        }
        .subheader {
            font-family: 'Roboto', sans-serif;
            font-size: 22px;
            color: #555;
        }
        .card {
            background-color: #f4f4f4;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        .notification-box {
            background-color: #fff4f0;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #FF5733;
            font-family: 'Roboto', sans-serif;
        }
        .map-container {
            margin-top: 30px;
            background-color: #ffffff;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15);
        }
        .progress-bar {
            background-color: #4CAF50;
            border-radius: 25px;
            height: 25px;
            width: 100%;
        }
        .btn-container {
            display: flex;
            justify-content: flex-start;
            margin-top: 20px;
        }
        .btn-container a {
            font-weight: bold;
            padding: 12px 24px;
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            text-decoration: none;
        }
        .btn-container a:hover {
            background-color: #45a049;
        }
    </style>
""", unsafe_allow_html=True)

# Function to preprocess the dataset
def preprocess_dataset(df):
    df = df.dropna(subset=["lattitude", "longitude"])
    df["lattitude"] = pd.to_numeric(df["lattitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["lattitude", "longitude"])
    return df

# Function to find the nearest charging station
def find_nearest_station(user_location, stations_df):
    stations_df["distance_km"] = stations_df.apply(
        lambda row: geodesic(user_location, (row["lattitude"], row["longitude"])).kilometers, axis=1
    )
    nearest_station = stations_df.loc[stations_df["distance_km"].idxmin()]
    return nearest_station, stations_df.nsmallest(5, "distance_km")

# Sidebar Section
with st.sidebar:
    st.image("https://i.imgur.com/vnIHKPf.png", width=200)  # Placeholder for a logo
    st.title("EV Finder ⚡")
    st.markdown(
        """
        *Find the nearest EV charging station* with just a few clicks.
        - 🚗 Battery percentage slider
        - 📍 Nearest station map view
        - ⚠ Battery alert notifications
        """
    )
    st.write("### Contact Us:")
    st.markdown(
        """
        - 📧 support@evfinder.com
        - 📞 123-456-7890
        """
    )

# Main Content Area
st.markdown('<div class="title">EV Charging Station Finder</div>', unsafe_allow_html=True)

# Battery Visualization
battery_percentage = st.slider("🔋 Set Your Battery Percentage", 0, 100, 50, key="battery_slider")
st.markdown(f"<div class='progress-bar' style='width:{battery_percentage}%'></div>", unsafe_allow_html=True)

# Dataset Path
DATASET_PATH = "ev-charging-stations-india.csv"

# Initialize notification flags
if 'notified_20' not in st.session_state:
    st.session_state.notified_20 = False
if 'notified_10' not in st.session_state:
    st.session_state.notified_10 = False

# Load the dataset
try:
    stations_df = pd.read_csv(DATASET_PATH)
    required_columns = ["name", "state", "city", "address", "lattitude", "longitude", "type"]

    if not all(col in stations_df.columns for col in required_columns):
        st.error(f"Dataset must contain columns: {', '.join(required_columns)}")
    else:
        stations_df = preprocess_dataset(stations_df)

        # Fetch user's location
        g = geocoder.ip("me")
        if g.ok:
            user_location = g.latlng

            # Battery Alerts and Notifications
            col1, col2 = st.columns([3, 1])  # Layout columns for better space management

            # Notify at 20% battery
            if battery_percentage <= 20 and not st.session_state.notified_20:
                st.session_state.notified_20 = True
                notification.notify(
                    title="Battery Alert!",
                    message="Your EV battery is below 20%. Find a charging station nearby!",
                    timeout=10
                )

            # Notify at 10% battery
            if battery_percentage <= 10 and not st.session_state.notified_10:
                st.session_state.notified_10 = True
                notification.notify(
                    title="Battery Alert!",
                    message="Your EV battery is below 10%. Find a charging station urgently!",
                    timeout=10
                )

            if battery_percentage < 20:  # Only show when battery is below 20%
                with col1:
                    st.subheader("📍 Nearest Charging Station")
                    nearest_station, top_stations = find_nearest_station(user_location, stations_df)

                    st.markdown(f"<div class='header'>{nearest_station['name']}</div>", unsafe_allow_html=True)
                    st.write(f"*Address:* {nearest_station['address']}, {nearest_station['city']}")
                    st.write(f"*Type:* {nearest_station['type']}")
                    st.write(f"*Distance:* {nearest_station['distance_km']:.2f} km")

                    # Display map
                    st.write('<div class="map-container">', unsafe_allow_html=True)
                    m = folium.Map(location=user_location, zoom_start=12)
                    folium.Marker(user_location, popup="You are here!", icon=folium.Icon(color="blue")).add_to(m)
                    station_location = (nearest_station["lattitude"], nearest_station["longitude"])
                    folium.Marker(
                        station_location,
                        popup=nearest_station["name"],
                        icon=folium.Icon(color="green"),
                    ).add_to(m)
                    st_folium(m, width=700, height=400)
                    st.write('</div>', unsafe_allow_html=True)

                    # Display Top 5 Stations
                    st.subheader("🏆 Top 5 Nearest Charging Stations")
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.dataframe(
                        top_stations[["name", "address", "city", "distance_km"]]
                        .rename(columns={"distance_km": "Distance (km)"})
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

                with col2:
                    # Remove extra button and directly show link
                    navigation_url = f"https://www.google.com/maps/dir/{user_location[0]},{user_location[1]}/{nearest_station['lattitude']},{nearest_station['longitude']}"
                    
                    # Link to Google Maps for navigation
                    st.markdown(
                        f'<a href="{navigation_url}" target="_blank"><div class="btn-container"><button>Start Navigation</button></div></a>',
                        unsafe_allow_html=True
                    )

        else:
            st.error("Unable to fetch your location. Please enable location services.")

except FileNotFoundError:
    st.error("Dataset file not found! Make sure 'ev-charging-stations-india.csv' exists.")