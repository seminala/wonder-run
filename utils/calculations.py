from math import radians, sin, cos, asin, sqrt, atan2, degrees
import math

EARTH_R = 6371.0  # km

def haversine_distance(lat1, lon1, lat2, lon2):
    # returns distance in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(min(1, sqrt(a)))
    return EARTH_R * c

def destination_point(lat, lon, bearing_deg, distance_km):
    # returns lat2, lon2 of point at distance_km and bearing from start (in degrees)
    # Using spherical Earth projected
    lat1 = radians(lat)
    lon1 = radians(lon)
    bearing = radians(bearing_deg)
    dr = distance_km / EARTH_R
    lat2 = asin(sin(lat1) * cos(dr) + cos(lat1) * sin(dr) * cos(bearing))
    lon2 = lon1 + atan2(sin(bearing) * sin(dr) * cos(lat1), cos(dr) - sin(lat1) * sin(lat2))
    return degrees(lat2), (degrees(lon2) + 540) % 360 - 180  # normalize to [-180,180]

def calculate_calories(distance_km, weight_kg):
    # Simple estimate: calories = distance_km * weight_kg * 1.036
    return distance_km * weight_kg * 1.036

def calculate_time_from_speed(distance_km, speed_kmh):
    if speed_kmh <= 0:
        return None
    hours = distance_km / speed_kmh
    return hours * 60.0

def rank_routes(routes, goal_type, target_value, weight_kg, speed_kmh):
    # routes: list of dicts with keys distance_km, duration_min, calories
    # returns index of best route
    scores = []
    for r in routes:
        if goal_type == "Distance (km)":
            score = abs(r["distance_km"] - float(target_value))
        elif goal_type == "Duration (minutes)":
            score = abs(r["duration_min"] - float(target_value))
        else:  # Calories
            score = abs(r["calories"] - float(target_value))
        # small tie-breaker prefer shorter duration
        score += r["duration_min"] * 0.01
        scores.append(score)
    # return index of minimum score
    best_index = int(min(range(len(scores)), key=lambda i: scores[i]))
    return best_index
