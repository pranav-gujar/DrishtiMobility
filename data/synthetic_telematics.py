"""
Realistic telematics and traffic scenario generators for Indian urban conditions.
Reflects Indian road realities: two-wheeler cut-ins, sudden braking, night fatigue,
and high PCU intersection bottlenecks.
"""
from typing import List, Dict, Any
from app.schemas.mobility import (
    DriverFacialTelemetry,
    VehicleKinematics,
    TrafficJunctionState,
)

# 4 Distinct Indian Driving Scenarios
TRIP_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "SCN-MUMBAI-SMOOTH": {
        "title": "Mumbai WEH Morning Commute (Attentive Driver)",
        "driver_name": "Aditya Sharma",
        "vehicle": "Maruti Suzuki Grand Vitara Intelligent Hybrid",
        "route": "Borivali to Bandra Kurla Complex (BKC)",
        "traffic_condition": "Moderate Flow, Stop-and-Go",
        "description": "Exemplary lane discipline, high attentiveness, continuous forward gaze, smooth regenerative braking.",
        "expected_score": 96.5,
        "rewards_tier": "Diamond",
        "ear_profile": {"mean": 0.32, "variance": 0.02, "drowsy_spikes": False},
        "mar_profile": {"mean": 0.18, "yawn_spikes": False},
        "phone_distraction": False,
        "harsh_events": 0,
    },
    "SCN-EXPRESSWAY-DROWSY": {
        "title": "Mumbai-Pune Expressway Late Night (Fatigued / Microsleep)",
        "driver_name": "Rohan Deshmukh",
        "vehicle": "Maruti Suzuki Brezza ZXi+ AT",
        "route": "Navi Mumbai to Lonavala Ghat",
        "traffic_condition": "Free Flow, High Speed (88 km/h)",
        "description": "Prolonged eye closure (EAR < 0.20 for >2.5s), head pitch drops, frequent yawning (MAR > 0.65). Early fatigue alert triggered.",
        "expected_score": 58.0,
        "rewards_tier": "Silver",
        "ear_profile": {"mean": 0.18, "variance": 0.05, "drowsy_spikes": True},
        "mar_profile": {"mean": 0.62, "yawn_spikes": True},
        "phone_distraction": False,
        "harsh_events": 2,
    },
    "SCN-DELHI-DISTRACTED": {
        "title": "Delhi Ring Road Evening (Mobile Phone Distraction)",
        "driver_name": "Vikram Singh",
        "vehicle": "Maruti Suzuki Fronx 1.0L Turbo Boosterjet",
        "route": "Dhaula Kuan to Nehru Place",
        "traffic_condition": "Dense Urban Corridor",
        "description": "Head yaw tilted down right (-34 deg), phone detected in lap, gaze diverted from road >3.2s, resulting in emergency harsh braking (-0.58g).",
        "expected_score": 64.2,
        "rewards_tier": "Bronze",
        "ear_profile": {"mean": 0.29, "variance": 0.03, "drowsy_spikes": False},
        "mar_profile": {"mean": 0.20, "yawn_spikes": False},
        "phone_distraction": True,
        "harsh_events": 3,
    },
    "SCN-BLR-RECKLESS-WEAVING": {
        "title": "Bengaluru Outer Ring Road (Aggressive Lane Weaving)",
        "driver_name": "Karthik Nair",
        "vehicle": "Maruti Suzuki Baleno Alpha AGS",
        "route": "Marathahalli to Bellandur Tech Corridor",
        "traffic_condition": "Choked Intersections, Sudden Openings",
        "description": "Rapid lane changes without indicator, solid yellow line crossing, high lateral acceleration (0.42g), stop-line overrun at junction.",
        "expected_score": 49.5,
        "rewards_tier": "Needs Coaching",
        "ear_profile": {"mean": 0.31, "variance": 0.02, "drowsy_spikes": False},
        "mar_profile": {"mean": 0.19, "yawn_spikes": False},
        "phone_distraction": False,
        "harsh_events": 5,
    },
}

# 4 Real-World Synchronized Arterial Junctions
CORRIDOR_JUNCTIONS: List[Dict[str, Any]] = [
    {
        "junction_id": "JNC-WEH-ANDHERI",
        "junction_name": "Andheri East Western Express Flyover Junction",
        "city": "Mumbai",
        "corridor_name": "Western Express Highway Arterial",
        "north_queue_pcu": 185,
        "south_queue_pcu": 240,
        "east_queue_pcu": 95,
        "west_queue_pcu": 110,
        "current_active_phase": "NORTH_SOUTH",
        "elapsed_green_seconds": 38,
        "current_cycle_seconds": 130,
        "congestion_level": "CONGESTED",
    },
    {
        "junction_id": "JNC-WEH-SANTACRUZ",
        "junction_name": "Santacruz Domestic Airport Crossroad",
        "city": "Mumbai",
        "corridor_name": "Western Express Highway Arterial",
        "north_queue_pcu": 140,
        "south_queue_pcu": 165,
        "east_queue_pcu": 80,
        "west_queue_pcu": 75,
        "current_active_phase": "NORTH_SOUTH",
        "elapsed_green_seconds": 24,
        "current_cycle_seconds": 110,
        "congestion_level": "MODERATE",
    },
    {
        "junction_id": "JNC-WEH-KALANAGAR",
        "junction_name": "Bandra Kalanagar Flyover Chokepoint",
        "city": "Mumbai",
        "corridor_name": "Western Express Highway Arterial",
        "north_queue_pcu": 290,
        "south_queue_pcu": 310,
        "east_queue_pcu": 160,
        "west_queue_pcu": 145,
        "current_active_phase": "NORTH_SOUTH",
        "elapsed_green_seconds": 55,
        "current_cycle_seconds": 150,
        "congestion_level": "GRIDLOCK",
    },
    {
        "junction_id": "JNC-WEH-BKC-CONN",
        "junction_name": "BKC Connector Entry Interchange",
        "city": "Mumbai",
        "corridor_name": "Western Express Highway Arterial",
        "north_queue_pcu": 120,
        "south_queue_pcu": 130,
        "east_queue_pcu": 210,
        "west_queue_pcu": 190,
        "current_active_phase": "EAST_WEST",
        "elapsed_green_seconds": 42,
        "current_cycle_seconds": 120,
        "congestion_level": "CONGESTED",
    },
]


def get_trip_telemetry_stream(scenario_id: str, steps: int = 15) -> List[Dict[str, Any]]:
    """Generates a sequential stream of driver facial + kinematics telemetry for a scenario."""
    if scenario_id not in TRIP_SCENARIOS:
        scenario_id = "SCN-MUMBAI-SMOOTH"
    
    cfg = TRIP_SCENARIOS[scenario_id]
    stream = []
    
    base_speed = 52.0 if "SMOOTH" in scenario_id else (85.0 if "EXPRESSWAY" in scenario_id else 38.0)
    
    for i in range(steps):
        # Time progression
        time_offset = i * 2.0  # 2 second intervals
        
        # Facial telemetry
        if cfg["ear_profile"]["drowsy_spikes"] and i >= 5:
            ear = max(0.12, cfg["ear_profile"]["mean"] - 0.015 * (i - 5))
            blink_ms = 450.0 + (i - 5) * 80.0
            gaze = False
            pitch = -18.0 - (i - 5) * 2.0
            yaw = 4.0
        elif cfg["phone_distraction"] and 4 <= i <= 9:
            ear = 0.28
            blink_ms = 180.0
            gaze = False
            pitch = -26.0
            yaw = -32.0  # looking down at passenger seat/lap
        else:
            ear = cfg["ear_profile"]["mean"] + (0.01 if i % 2 == 0 else -0.01)
            blink_ms = 150.0 + (i % 3) * 20.0
            gaze = True
            pitch = -2.0
            yaw = 1.0
            
        mar = cfg["mar_profile"]["mean"]
        if cfg["mar_profile"]["yawn_spikes"] and 6 <= i <= 10:
            mar = 0.72  # deep yawn
            
        phone = True if (cfg["phone_distraction"] and 4 <= i <= 9) else False
        
        # Kinematics
        if cfg["phone_distraction"] and i == 10:
            # Emergency harsh brake after looking up from phone
            long_g = -0.58
            speed = max(10.0, base_speed - 28.0)
            lat_g = 0.08
        elif "WEAVING" in scenario_id and i % 3 == 0:
            long_g = 0.28
            speed = base_speed + 12.0
            lat_g = 0.44  # aggressive swerve
        else:
            long_g = 0.04 if i % 2 == 0 else -0.03
            speed = base_speed + (i % 4) * 1.5
            lat_g = 0.05
            
        stream.append({
            "step": i + 1,
            "seconds_elapsed": time_offset,
            "facial": {
                "ear_mean": round(ear, 3),
                "mar": round(mar, 3),
                "blink_duration_ms": round(blink_ms, 1),
                "head_yaw_deg": round(yaw, 1),
                "head_pitch_deg": round(pitch, 1),
                "phone_detected": phone,
                "gaze_on_road": gaze,
            },
            "kinematics": {
                "speed_kmh": round(speed, 1),
                "accel_longitudinal_g": round(long_g, 2),
                "accel_lateral_g": round(lat_g, 2),
                "steering_angle_deg": round(lat_g * 45.0, 1),
                "turn_indicator_active": True if (i == 3 and "SMOOTH" in scenario_id) else False,
            }
        })
        
    return stream


def get_junction_network_state() -> List[TrafficJunctionState]:
    """Returns validated state models of all 4 corridor junctions."""
    return [TrafficJunctionState(**j) for j in CORRIDOR_JUNCTIONS]
