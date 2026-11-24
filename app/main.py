"""
FastAPI application for DrishtiMobility.
Integrates Driver In-Cabin Monitoring, Computer Vision Lane Discipline,
Webster Traffic Signal Optimization, and Cellular V2X Mesh Broadcasts.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
import json
from typing import Dict, Any, List

from app.schemas.mobility import (
    DriverFacialTelemetry,
    VehicleKinematics,
    TrafficJunctionState,
)
from app.engine.driver_monitor import (
    assess_driver_fatigue,
    calculate_driver_safety_score,
)
from app.engine.lane_discipline import (
    detect_lane_violation,
    issue_educational_challan,
)
from app.engine.traffic_signal import (
    compute_adaptive_signal_plan,
    optimize_corridor_network,
)
from app.engine.v2x_alerts import (
    get_relevant_v2x_alerts,
)
from data.synthetic_telematics import (
    TRIP_SCENARIOS,
    CORRIDOR_JUNCTIONS,
    get_trip_telemetry_stream,
    get_junction_network_state,
)

app = FastAPI(
    title="DrishtiMobility API",
    description="Edge AI Connected Vehicle & Intelligent Urban Traffic Safety Platform for Maruti Suzuki Innovation Challenge",
    version="1.0.0",
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "ml", "artifacts")


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "platform": "DrishtiMobility",
        "partner": "Maruti Suzuki Innovation x IIT Bombay E-Summit 2026",
        "modules": [
            "Edge AI Driver Fatigue Monitor",
            "CV Lane Discipline Engine",
            "Webster Adaptive Traffic Optimization",
            "Cellular V2X Mesh Alerts",
        ]
    }


@app.get("/api/scenarios")
def list_scenarios():
    return [
        {
            "id": k,
            "title": v["title"],
            "driver": v["driver_name"],
            "vehicle": v["vehicle"],
            "route": v["route"],
            "condition": v["traffic_condition"],
            "description": v["description"],
            "expected_score": v["expected_score"],
            "rewards_tier": v["rewards_tier"],
        }
        for k, v in TRIP_SCENARIOS.items()
    ]


@app.get("/api/scenarios/{scenario_id}/telemetry")
def get_scenario_telemetry(scenario_id: str, steps: int = 15):
    if scenario_id not in TRIP_SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    stream = get_trip_telemetry_stream(scenario_id, steps=steps)
    scorecard = calculate_driver_safety_score(stream)
    return {
        "scenario": TRIP_SCENARIOS[scenario_id],
        "telemetry_stream": stream,
        "scorecard": scorecard.model_dump(),
    }


@app.post("/api/driver/evaluate")
def evaluate_driver_step(payload: Dict[str, Any]):
    facial = payload.get("facial", {})
    kinematics = payload.get("kinematics", {})
    speed = kinematics.get("speed_kmh", 50.0)

    alert = assess_driver_fatigue(facial, speed_kmh=speed)
    return {
        "fatigue_alert": alert.model_dump() if alert else None,
        "facial_telemetry": facial,
        "kinematics": kinematics,
    }


@app.get("/api/traffic/corridor")
def get_traffic_corridor():
    junctions = get_junction_network_state()
    optimization = optimize_corridor_network(junctions)
    return {
        "junctions": [j.model_dump() for j in junctions],
        "optimization": optimization,
    }


@app.post("/api/traffic/optimize")
def run_corridor_optimization():
    junctions = get_junction_network_state()
    return optimize_corridor_network(junctions)


@app.get("/api/v2x/alerts")
def get_v2x_alerts(lat: float = 19.0620, lon: float = 72.8530):
    return get_relevant_v2x_alerts(vehicle_lat=lat, vehicle_lon=lon)


@app.post("/api/lane/violation")
def check_lane_violation(payload: Dict[str, Any]):
    kinematics = payload.get("kinematics", {})
    lateral_offset = float(payload.get("lateral_offset_meters", 0.0))
    crossing_solid = bool(payload.get("crossing_solid_line", False))
    overrun_stop = bool(payload.get("overrunning_stop_line", False))
    speed_limit = float(payload.get("speed_limit_kmh", 80.0))

    event = detect_lane_violation(
        kinematics=kinematics,
        lateral_offset_meters=lateral_offset,
        crossing_solid_line=crossing_solid,
        overrunning_stop_line=overrun_stop,
        speed_limit_kmh=speed_limit,
    )
    if not event:
        return {"violation_detected": False, "event": None, "challan": None}

    challan = issue_educational_challan(event)
    return {
        "violation_detected": True,
        "event": event.model_dump(),
        "challan": challan.model_dump(),
    }


@app.get("/api/metrics")
def get_ml_metrics():
    metrics_path = os.path.join(ARTIFACTS_DIR, "metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="ML metrics not yet generated")
    with open(metrics_path, "r") as f:
        return json.load(f)


# Serve Static UI Dashboard
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_dashboard():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "DrishtiMobility API is online. Mount index.html in app/static."}
