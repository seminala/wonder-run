import streamlit as st
import requests
from datetime import datetime
import os
import streamlit as st
from utils.api_handler import geocode_address, get_directions, get_weather_by_coords
from utils.calculations import (
    haversine_distance,
    destination_point,
    calculate_calories,
    calculate_time_from_speed,
    rank_routes
)
from utils.map_renderer import (
    render_routes_map,
    decode_polyline,
    get_waypoints_from_polyline,
    create_google_maps_url,
    create_static_map_url
)
from streamlit_folium import st_folium
import folium
import pandas as pd
import base64

# -----------------------------------------------------------
# APP CONFIGURATION
# -----------------------------------------------------------
st.set_page_config(
    page_title="Wonder Run",
    page_icon="🏃",
    layout="wide"
)

# ----------------------
# Load API keys (env or st.secrets)
# ----------------------
GOOGLE_API_KEY = st.secrets.get("GOOGLE_MAPS_API_KEY")
OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHERMAP_API_KEY")

if not GOOGLE_API_KEY or not OPENWEATHER_API_KEY:
    st.error("Missing API keys in secrets.toml.")
    st.stop()

# Initialize session state for storing results
if 'routes_generated' not in st.session_state:
    st.session_state.routes_generated = False
if 'all_routes' not in st.session_state:
    st.session_state.all_routes = []
if 'best_index' not in st.session_state:
    st.session_state.best_index = 0
if 'origin_coords' not in st.session_state:
    st.session_state.origin_coords = None
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None

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
    try:
        with open(path, "rb") as file:
            data = file.read()
        return base64.b64encode(data).decode()
    except:
        return None

# Path to your GIF file (adjust if needed)
gif_data = load_gif("assets/hongyo.gif")

# -----------------------------------------------------------
# Header Layout
# -----------------------------------------------------------
if gif_data:
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
else:
    st.markdown("""
    <div class="header" style="text-align:center; padding-top:1rem; padding-bottom:1rem; border-bottom:2px solid #D2691E;">
        <span class="header-title" 
            style="font-size:2.5rem; font-weight:800; 
                    background: linear-gradient(90deg, #FF8C00, #FFD700); 
                    -webkit-background-clip: text; 
                    -webkit-text-fill-color: transparent;
                    vertical-align:middle;">
            🏃 Wonder Run
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

start_location = st.sidebar.text_input("Start Location (e.g., Condongcatur, Sleman)")
goal_type = st.sidebar.selectbox("Goal Type", ["Distance (km)", "Duration (minutes)", "Calories"])
target_value = st.sidebar.number_input("Target Value", min_value=1.0, step=0.5)
weight = st.sidebar.number_input("Your Weight (kg)", min_value=30.0, max_value=150.0, value=60.0)
speed_pref = st.sidebar.slider("Average Speed (km/h)", 5, 15, 8)
st.sidebar.markdown("---")

# -----------------------------------------------------------
# MAIN AREA: MAP AND ROUTE RESULTS
# -----------------------------------------------------------
st.markdown("### Suggested Routes Options")
generate = st.button("Generate Route")

# ----------------------
# Generate logic
# ----------------------
if generate:
    if not GOOGLE_API_KEY:
        st.error("Google Maps API key missing.")
    else:
        with st.spinner("Generating routes..."):
            # 1. Geocode start
            geocode = geocode_address(start_location, GOOGLE_API_KEY)
            if not geocode:
                st.error("Start location not found. Please refine the address.")
                st.session_state.routes_generated = False
            else:
                origin_lat, origin_lng = geocode["lat"], geocode["lng"]
                st.session_state.origin_coords = (origin_lat, origin_lng)

                # 2. Determine target distance depending on goal type
                if goal_type == "Distance (km)":
                    target_distance_km = float(target_value)
                elif goal_type == "Duration (minutes)":
                    # convert duration to distance using preferred speed
                    minutes = float(target_value)
                    target_distance_km = (minutes / 60.0) * speed_pref
                else:  # Calories
                    # approximate distance from calories: calories = distance_km * weight * 1.036
                    target_distance_km = float(target_value) / (weight * 1.036)

                # 3. Generate candidate destinations by bearings
                n_bearings = 8
                bearings = [i * (360 / n_bearings) for i in range(n_bearings)]
                candidates = []
                for bearing in bearings:
                    dest_lat, dest_lng = destination_point(origin_lat, origin_lng, bearing, target_distance_km / 2.0)
                    # aim for half distance away to encourage roundtrip-ish route (origin->point)
                    candidates.append((dest_lat, dest_lng))

                # 4. Request Directions for each candidate (origin -> candidate)
                all_routes = []
                for idx, (dlat, dlng) in enumerate(candidates):
                    directions = get_directions(
                        origin=(origin_lat, origin_lng),
                        destination=(dlat, dlng),
                        api_key=GOOGLE_API_KEY,
                        alternatives=True
                    )
                    if not directions:
                        continue
                    # directions may have multiple route alternatives
                    for r in directions:
                        # distance in km, duration in minutes
                        dist_km = r["distance_m"] / 1000.0
                        dur_min = r["duration_s"] / 60.0
                        est_cal = calculate_calories(dist_km, weight)
                        all_routes.append({
                            "route_id": f"{idx}-{r['route_index']}",
                            "polyline": r["polyline"],
                            "distance_km": round(dist_km, 3),
                            "duration_min": round(dur_min, 1),
                            "calories": round(est_cal, 1),
                            "summary": r.get("summary", "")
                        })

                if not all_routes:
                    st.error("No routes were returned from the Directions API. Try another start location or increase candidate bearings.")
                    st.session_state.routes_generated = False
                else:
                    # 5. Rank routes based on goal and target
                    best_index = rank_routes(all_routes, goal_type, target_value, weight, speed_pref)

                    # Store in session state
                    st.session_state.all_routes = all_routes
                    st.session_state.best_index = best_index
                    st.session_state.routes_generated = True

                    # 8. Weather at origin
                    if OPENWEATHER_API_KEY:
                        w = get_weather_by_coords(lat=origin_lat, lon=origin_lng, api_key=OPENWEATHER_API_KEY)
                        st.session_state.weather_data = w

# Display results if routes have been generated
if st.session_state.routes_generated:
    all_routes = st.session_state.all_routes
    best_index = st.session_state.best_index
    origin_lat, origin_lng = st.session_state.origin_coords

    # Display weather at top
    if st.session_state.weather_data:
        w = st.session_state.weather_data
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; color: white;">
            <h3 style="margin: 0; color: white;">🌤️ Current Weather at Start Location</h3>
            <div style="display: flex; gap: 2rem; margin-top: 1rem; flex-wrap: wrap;">
                <div><strong>Location:</strong> {w['name']}</div>
                <div><strong>Temperature:</strong> {w['temp']} °C</div>
                <div><strong>Humidity:</strong> {w['humidity']}%</div>
                <div><strong>Condition:</strong> {w['condition']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Show best route recommendation
    best_route = all_routes[best_index]
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #FF8C00 0%, #FFD700 100%); 
                padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; color: white;">
        <h3 style="margin: 0; color: white;">⭐ Recommended Route</h3>
        <div style="display: flex; gap: 2rem; margin-top: 1rem; flex-wrap: wrap;">
            <div><strong>Route:</strong> {best_route['route_id']}</div>
            <div><strong>Distance:</strong> {best_route['distance_km']} km</div>
            <div><strong>Duration:</strong> {best_route['duration_min']} min</div>
            <div><strong>Calories:</strong> {best_route['calories']} kcal</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Display routes in columns (3 per row)
    st.markdown("### 📍 All Route Options")
    
    # Sort routes by distance
    sorted_routes = sorted(enumerate(all_routes), key=lambda x: x[1]['distance_km'])
    
    # Display in rows of 3 columns
    for i in range(0, len(sorted_routes), 3):
        cols = st.columns(3)
        
        for col_idx, col in enumerate(cols):
            route_idx = i + col_idx
            if route_idx < len(sorted_routes):
                original_idx, route = sorted_routes[route_idx]
                
                with col:
                    # Determine if this is the best route
                    is_best = original_idx == best_index
                    border_color = "#FF8C00" if is_best else "#D2691E"
                    
                    st.markdown(f"""
                    <div style="border: 3px solid {border_color}; 
                                border-radius: 12px; 
                                padding: 1rem; 
                                background-color: #FFF8F0;
                                margin-bottom: 1rem;
                                height: 100%;">
                        <h4 style="color: #3E2723; margin-top: 0;">
                            {'⭐ ' if is_best else ''}Route {route['route_id']}
                        </h4>
                        <div style="margin: 0.5rem 0;">
                            <strong>📏 Distance:</strong> {route['distance_km']} km<br>
                            <strong>⏱️ Duration:</strong> {route['duration_min']} min<br>
                            <strong>🔥 Calories:</strong> {route['calories']} kcal<br>
                            <strong>🛣️ Via:</strong> {route['summary'] if route['summary'] else 'Direct route'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Generate map preview for this route using Folium
                    try:
                        # Create a small folium map for this route
                        route_map = folium.Map(
                            location=[origin_lat, origin_lng],
                            zoom_start=13,
                            tiles='OpenStreetMap',
                            width=400,
                            height=300
                        )
                        
                        # Add start marker
                        folium.Marker(
                            [origin_lat, origin_lng],
                            popup="Start",
                            icon=folium.Icon(color="green", icon="play", prefix='fa')
                        ).add_to(route_map)
                        
                        # Decode and add route polyline
                        route_coords = decode_polyline(route['polyline'])
                        if route_coords:
                            route_color = "#FF8C00" if is_best else "#D2691E"
                            folium.PolyLine(
                                locations=route_coords,
                                color=route_color,
                                weight=4,
                                opacity=0.8
                            ).add_to(route_map)
                            
                            # Fit bounds to show entire route
                            route_map.fit_bounds(route_coords)
                        
                        # Display the map
                        st_folium(route_map, width=400, height=300, key=f"route_map_{route['route_id']}", returned_objects=[])
                        
                    except Exception as e:
                        # Fallback: show placeholder
                        st.markdown(f"""
                        <div style="background: #f0f0f0; height: 300px; display: flex; 
                                    align-items: center; justify-content: center; 
                                    border-radius: 8px; color: #666;">
                            <div style="text-align: center;">
                                <div style="font-size: 3rem;">🗺️</div>
                                <div>Map preview unavailable</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Decode polyline to get waypoints for directions URL
                    waypoints = get_waypoints_from_polyline(route['polyline'], num_waypoints=3)
                    
                    # Create Google Maps directions URL with waypoints (for a loop route)
                    if len(waypoints) >= 2:
                        # For a round trip: origin -> waypoint -> origin
                        mid_point = waypoints[len(waypoints)//2]
                        maps_link = create_google_maps_url(
                            origin=(origin_lat, origin_lng),
                            destination=(origin_lat, origin_lng),
                            waypoints=[mid_point],
                            mode='walking'
                        )
                    else:
                        maps_link = f"https://www.google.com/maps/dir/?api=1&origin={origin_lat},{origin_lng}&destination={origin_lat},{origin_lng}&travelmode=walking"
                    st.markdown(f"""
                    <a href="{maps_link}" target="_blank" 
                        style="display: inline-block; 
                            background-color: #FF8C00; 
                            color: white; 
                            padding: 0.5rem 1rem; 
                            text-decoration: none; 
                            border-radius: 8px; 
                            margin-top: 0.5rem;
                            text-align: center;
                            width: 100%;">
                        🗺️ Open in Google Maps
                    </a>
                    """, unsafe_allow_html=True)

else:
    st.info("Set your running goals in the sidebar and click 'Generate Route'.")

# -----------------------------------------------------------
# FOOTER
# -----------------------------------------------------------
st.markdown("""
<hr style="border:1px solid #D2691E;">
<div style="text-align:center; color:#3E2723;">
Made With Love ❤️ by Nabila Putri - For Aplikasi Web With Bu Akhsin
</div>
""", unsafe_allow_html=True)