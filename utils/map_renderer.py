import folium
from folium import Popup
import polyline
from branca.element import Figure

def render_routes_map(origin: tuple, routes: list, best_index: int = 0):
    # origin: (lat, lng)
    # routes: list of dicts with 'polyline' key (encoded polyline) and metadata
    m = folium.Map(location=[origin[0], origin[1]], zoom_start=13, control_scale=True)
    # add origin marker
    folium.CircleMarker(location=[origin[0], origin[1]], radius=6, color="#FF8C00", fill=True, fill_color="#FF8C00", popup="Start").add_to(m)

    colors = ["#FF7F50", "#FFD700", "#FF8C00", "#F5DEB3", "#D2691E", "#3E2723"]
    for i, r in enumerate(routes):
        try:
            coords = polyline.decode(r["polyline"])
        except Exception:
            coords = []
        if not coords:
            continue
        color = colors[i % len(colors)]
        weight = 5 if i == best_index else 3
        folium.PolyLine(locations=coords, color=color, weight=weight, opacity=0.8, popup=f"Route {r['route_id']}").add_to(m)
        # add popup at midpoint
        mid = coords[len(coords)//2]
        popup_html = f"<b>Route {r['route_id']}</b><br>Distance: {r['distance_km']} km<br>Duration: {r['duration_min']} min<br>Calories: {r['calories']} kcal"
        folium.Marker(location=mid, icon=folium.DivIcon(html=f"""<div style="font-size:12px;background:white;padding:4px;border-radius:6px;border:1px solid #D2691E;">{r['route_id']}</div>"""), popup=Popup(popup_html, max_width=250)).add_to(m)
    return m


def decode_polyline(polyline_str):
    """
    Decode a polyline string into a list of (lat, lng) coordinates.
    Uses the polyline library for decoding.
    
    Args:
        polyline_str: Encoded polyline string from Google Maps API
        
    Returns:
        List of tuples: [(lat1, lng1), (lat2, lng2), ...]
    """
    try:
        return polyline.decode(polyline_str)
    except Exception:
        return []


def get_waypoints_from_polyline(polyline_str, num_waypoints=5):
    """
    Extract evenly spaced waypoints from a polyline for route visualization.
    
    Args:
        polyline_str: Encoded polyline string
        num_waypoints: Number of waypoints to extract (default: 5)
        
    Returns:
        List of (lat, lng) tuples representing waypoints
    """
    coordinates = decode_polyline(polyline_str)
    
    if not coordinates:
        return []
    
    if len(coordinates) <= num_waypoints:
        return coordinates
    
    # Extract evenly spaced waypoints
    step = len(coordinates) // (num_waypoints - 1)
    waypoints = [coordinates[i * step] for i in range(num_waypoints - 1)]
    waypoints.append(coordinates[-1])  # Always include the last point
    
    return waypoints


def create_google_maps_url(origin, destination, waypoints=None, mode='walking'):
    """
    Create a Google Maps URL with directions and waypoints.
    
    Args:
        origin: Tuple of (lat, lng) for start point
        destination: Tuple of (lat, lng) for end point
        waypoints: List of (lat, lng) tuples for intermediate points
        mode: Travel mode (walking, driving, bicycling, transit)
        
    Returns:
        String: Google Maps URL
    """
    base_url = "https://www.google.com/maps/dir/?api=1"
    origin_str = f"&origin={origin[0]},{origin[1]}"
    dest_str = f"&destination={destination[0]},{destination[1]}"
    mode_str = f"&travelmode={mode}"
    
    # Add waypoints if provided
    waypoint_str = ""
    if waypoints and len(waypoints) > 0:
        waypoint_coords = "|".join([f"{lat},{lng}" for lat, lng in waypoints])
        waypoint_str = f"&waypoints={waypoint_coords}"
    
    return base_url + origin_str + dest_str + waypoint_str + mode_str


def create_static_map_url(center, zoom=14, size="400x300", markers=None, path=None, api_key=""):
    """
    Create a Google Static Maps API URL.
    
    Args:
        center: Tuple of (lat, lng) for map center
        zoom: Zoom level (1-20)
        size: Size string like "400x300"
        markers: List of marker dicts with 'lat', 'lng', 'label', 'color'
        path: Encoded polyline string or list of coordinates
        api_key: Google Maps API key
        
    Returns:
        String: Static map URL
    """
    base_url = f"https://maps.googleapis.com/maps/api/staticmap?"
    params = [
        f"center={center[0]},{center[1]}",
        f"zoom={zoom}",
        f"size={size}",
        "maptype=roadmap"
    ]
    
    # Add markers
    if markers:
        for marker in markers:
            color = marker.get('color', 'red')
            label = marker.get('label', '')
            lat = marker['lat']
            lng = marker['lng']
            params.append(f"markers=color:{color}|label:{label}|{lat},{lng}")
    
    # Add path
    if path:
        if isinstance(path, str):
            # It's an encoded polyline
            params.append(f"path=color:0xff8c00|weight:4|enc:{path}")
        elif isinstance(path, list):
            # It's a list of coordinates
            path_str = "|".join([f"{lat},{lng}" for lat, lng in path])
            params.append(f"path=color:0xff8c00|weight:4|{path_str}")
    
    params.append(f"key={api_key}")
    
    return base_url + "&".join(params)