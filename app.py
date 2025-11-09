import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
import base64

# -----------------------------------------------------------
# APP CONFIGURATION
# -----------------------------------------------------------
st.set_page_config(
    page_title="Wonder Run",
    page_icon="🏃",
    layout="wide"
)

# -----------------------------------------------------------
# CUSTOM CSS FOR THEME AND GRADIENT HEADER
# -----------------------------------------------------------
st.markdown("""
    <style>
    /* General page styling */
    body {
        background-color: #FFFFFF;
        color: #3E2723;
        font-family: 'Poppins', sans-serif;
    }

    /* Header */
    .header {
        text-align: center;
        padding-top: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #D2691E;
    }

    .header-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF8C00, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        vertical-align: middle;
    }

    .header-subtitle {
        color: #3E2723;
        font-size: 1rem;
        font-weight: 500;
        margin-top: -5px;
    }

    .gif-icon {
        width: 50px;
        vertical-align: middle;
        margin-right: 10px;
    }

    /* Buttons */
    div.stButton > button:first-child {
        background-color: #FF8C00;
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        font-size: 1rem;
        border-radius: 10px;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #FFD700;
        color: #3E2723;
    }

    /* Cards */
    .card {
        background-color: #FFE4C4;
        border: 1px solid #D2691E;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
    }

    .route-card {
        background-color: #FFFFFF;
        border-left: 6px solid #FF7F50;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }

    .best-route {
        border-left: 6px solid #FF8C00 !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# Load Local GIF for Header
# -----------------------------------------------------------
def load_gif(path):
    with open(path, "rb") as file:
        data = file.read()
    return base64.b64encode(data).decode()

# Path to your GIF file (adjust if needed)
gif_data = load_gif("assets/hongyo.gif")

# -----------------------------------------------------------
# Header Layout
# -----------------------------------------------------------
st.markdown(f"""
<div class="header" style="text-align:center; padding-top:1rem; padding-bottom:1rem; border-bottom:2px solid #D2691E;">
    <img src="data:image/gif;base64,{gif_data}" class="gif-icon" style="width:60px; vertical-align:middle; margin-right:10px;" />
    <span class="header-title" 
        style="font-size:2.5rem; font-weight:800; 
                background: linear-gradient(90deg, #FF8C00, #FFD700); 
                -webkit-background-clip: text; 
                -webkit-text-fill-color: transparent;
                vertical-align:middle;">
        Wonder Run
    </span>
    <div class="header-subtitle" 
        style="color:#3E2723; font-size:1rem; font-weight:500; margin-top:4px;">
        Personalized Running Routes for Your Fitness Goals
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------
# SIDEBAR: USER INPUT
# -----------------------------------------------------------
st.sidebar.header("Plan Your Run")

start_location = st.sidebar.text_input("Start Location (e.g., Jakarta, Indonesia)")
goal_type = st.sidebar.selectbox("Goal Type", ["Distance (km)", "Duration (minutes)", "Calories"])
target_value = st.sidebar.number_input("Target Value", min_value=1.0, step=0.5)
weight = st.sidebar.number_input("Your Weight (kg)", min_value=30.0, max_value=150.0, value=60.0)
speed_pref = st.sidebar.slider("Average Speed (km/h)", 5, 15, 8)
st.sidebar.markdown("---")

# Weather info placeholder
st.sidebar.subheader("Weather Information")
city_weather = st.sidebar.text_input("Check Weather for City", "")
show_weather = st.sidebar.button("Get Weather Info")

if show_weather and city_weather:
    # Example API call (OpenWeatherMap)
    api_key = "your_openweather_api_key"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_weather}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("cod") == 200:
            st.sidebar.markdown(f"**Temperature:** {data['main']['temp']} °C")
            st.sidebar.markdown(f"**Humidity:** {data['main']['humidity']}%")
            st.sidebar.markdown(f"**Condition:** {data['weather'][0]['main']}")
        else:
            st.sidebar.warning("City not found.")
    except:
        st.sidebar.error("Error fetching weather data.")

# -----------------------------------------------------------
# MAIN AREA: MAP AND ROUTE RESULTS
# -----------------------------------------------------------
st.markdown("### Suggested Routes")

# Generate button
if st.button("Generate Route"):
    # Mock data for demonstration
    route_data = pd.DataFrame({
        "Route": ["A", "B", "C"],
        "Distance (km)": [target_value * 0.9, target_value, target_value * 1.1],
        "Estimated Time (min)": [round((target_value * 60) / speed_pref, 1)] * 3,
        "Calories Burned": [round(weight * target_value * 1.036, 1)] * 3
    })

    # Display routes
    for i, row in route_data.iterrows():
        css_class = "route-card best-route" if i == 1 else "route-card"
        st.markdown(f"""
        <div class="{css_class}">
            <strong>Route {row['Route']}</strong><br>
            Distance: {row['Distance (km)']} km<br>
            Estimated Time: {row['Estimated Time (min)']} minutes<br>
            Calories Burned: {row['Calories Burned']} kcal
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("Set your running goals in the sidebar and click 'Generate Route'.")

# -----------------------------------------------------------
# FOOTER
# -----------------------------------------------------------
st.markdown("""
<hr style="border:1px solid #D2691E;">
<div style="text-align:center; color:#3E2723;">
Powered by Google Maps API & OpenWeatherMap API
</div>
""", unsafe_allow_html=True)
