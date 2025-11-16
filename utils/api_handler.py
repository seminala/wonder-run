import requests
from typing import Optional, Tuple, List, Dict
import polyline

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
OWM_URL = "https://api.openweathermap.org/data/2.5/weather"

def geocode_address(address: str, api_key: str) -> Optional[dict]:
    params = {"address": address, "key": api_key}
    try:
        r = requests.get(GEOCODE_URL, params=params, timeout=10)
        data = r.json()
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return {"lat": loc["lat"], "lng": loc["lng"], "formatted_address": data["results"][0]["formatted_address"]}
    except Exception:
        return None
    return None

def parse_directions_response(json_data: dict) -> List[dict]:
    routes = []
    if json_data.get("status") != "OK":
        return routes
    for idx, r in enumerate(json_data.get("routes", [])):
        # compute total distance and duration
        legs = r.get("legs", [])
        total_distance = sum([leg.get("distance", {}).get("value", 0) for leg in legs])  # meters
        total_duration = sum([leg.get("duration", {}).get("value", 0) for leg in legs])  # seconds
        # get overview_polyline
        overview_poly = r.get("overview_polyline", {}).get("points")
        summary = r.get("summary", "")
        routes.append({
            "route_index": idx,
            "distance_m": total_distance,
            "duration_s": total_duration,
            "polyline": overview_poly,
            "summary": summary
        })
    return routes

def get_directions(origin: Tuple[float, float], destination: Tuple[float, float], api_key: str, alternatives: bool = True) -> Optional[List[dict]]:
    origin_str = f"{origin[0]},{origin[1]}"
    dest_str = f"{destination[0]},{destination[1]}"
    params = {
        "origin": origin_str,
        "destination": dest_str,
        "key": api_key,
        "alternatives": str(alternatives).lower(),
        "mode": "walking"  # walking/jogging is closer to running
    }
    try:
        r = requests.get(DIRECTIONS_URL, params=params, timeout=10)
        data = r.json()
        return parse_directions_response(data)
    except Exception:
        return None

def get_weather_by_coords(lat: float = None, lon: float = None, city: str = None, api_key: str = None) -> Optional[dict]:
    if not api_key:
        return None
    params = {"appid": api_key, "units": "metric"}
    if city:
        params["q"] = city
    elif lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    else:
        return None
    try:
        r = requests.get(OWM_URL, params=params, timeout=8)
        data = r.json()
        if data.get("cod") in (200, "200"):
            return {
                "name": data.get("name"),
                "temp": data.get("main", {}).get("temp"),
                "humidity": data.get("main", {}).get("humidity"),
                "condition": data.get("weather", [{}])[0].get("main")
            }
    except Exception:
        return None
    return None
