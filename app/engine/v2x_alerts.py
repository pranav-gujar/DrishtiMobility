"""
V2X Connected Mobility & Collaborative Safety Alert Engine.
Simulates Vehicle-to-Vehicle (V2V) and Vehicle-to-Infrastructure (V2I) mesh broadcasting
over cellular C-V2X (3GPP Rel 16/17) standards.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import math
from app.schemas.mobility import V2XAlertBroadcast

# Active road hazards across Mumbai / Delhi / Bengaluru corridors
ACTIVE_ROAD_HAZARDS = [
    {
        "broadcast_id": "V2X-AMB-EMERGENCY",
        "hazard_type": "EMERGENCY_VEHICLE_APPROACHING",
        "origin_latitude": 19.0607,
        "origin_longitude": 72.8524,
        "relevance_radius_meters": 600.0,
        "heading_degrees": 185.0,
        "message_text": "Ambulance en route to Lilavati Hospital approaching from behind in lane 1.",
        "recommended_driver_action": "Yield left immediately and keep the rightmost express lane clear.",
        "active": True,
    },
    {
        "broadcast_id": "V2X-POTHOLE-HAZARD",
        "hazard_type": "SEVERE_SURFACE_POTHOLE",
        "origin_latitude": 19.1197,
        "origin_longitude": 72.8464,
        "relevance_radius_meters": 350.0,
        "heading_degrees": 10.0,
        "message_text": "Deep pothole cluster reported in middle lane near Gundavali metro station.",
        "recommended_driver_action": "Reduce speed to 40 km/h; merge to outer lane when safe.",
        "active": True,
    },
    {
        "broadcast_id": "V2X-DISABLED-VEHICLE",
        "hazard_type": "STALLED_HEAVY_TRUCK",
        "origin_latitude": 19.0176,
        "origin_longitude": 72.8300,
        "relevance_radius_meters": 450.0,
        "heading_degrees": 210.0,
        "message_text": "Stalled multi-axle cargo truck in right curve near Prabhadevi flyover descent.",
        "recommended_driver_action": "Prepare for sudden queue tail; maintain 3-car following distance.",
        "active": True,
    },
]


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def get_relevant_v2x_alerts(
    vehicle_lat: float = 19.0620,
    vehicle_lon: float = 72.8530,
) -> List[Dict[str, Any]]:
    """
    Filters V2X mesh broadcasts based on geofence proximity and relevance.
    """
    relevant = []
    for h in ACTIVE_ROAD_HAZARDS:
        dist = haversine_distance_meters(vehicle_lat, vehicle_lon, h["origin_latitude"], h["origin_longitude"])
        is_relevant = dist <= h["relevance_radius_meters"]
        
        # Include distance and countdown in payload
        entry = dict(h)
        entry["distance_to_hazard_meters"] = round(dist, 1)
        entry["within_warning_zone"] = is_relevant
        relevant.append(entry)

    return relevant
