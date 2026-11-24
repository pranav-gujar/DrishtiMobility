"""
Automated Pytest verification suite for DrishtiMobility.
Tests Driver Fatigue Monitoring, Vehicle Kinematics, Lane Discipline e-Challans,
Webster Traffic Signal Optimization, and Cellular V2X Geofencing.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
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
    haversine_distance_meters,
)
from app.schemas.mobility import (
    FatigueState,
    AlertSeverity,
    LaneViolationType,
    TrafficJunctionState,
)
from data.synthetic_telematics import (
    get_trip_telemetry_stream,
    get_junction_network_state,
)

client = TestClient(app)


def test_api_health_and_metrics():
    """Verifies that health and ML metrics endpoints return valid schemas."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["platform"] == "DrishtiMobility"
    assert len(data["modules"]) == 4

    metrics_res = client.get("/api/metrics")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert "models" in metrics
    assert "Drishti_Gradient_Boosting" in metrics["models"]
    assert metrics["models"]["Drishti_Gradient_Boosting"]["roc_auc"] >= 0.95


def test_driver_fatigue_detection():
    """Tests Euro NCAP aligned fatigue and distraction detection logic."""
    # 1. Attentive state -> No alert
    attentive_fac = {"ear_mean": 0.32, "mar": 0.18, "blink_duration_ms": 150.0, "gaze_on_road": True}
    assert assess_driver_fatigue(attentive_fac) is None

    # 2. Critical Microsleep
    microsleep_fac = {"ear_mean": 0.12, "mar": 0.22, "blink_duration_ms": 2200.0, "gaze_on_road": False}
    alert_ms = assess_driver_fatigue(microsleep_fac)
    assert alert_ms is not None
    assert alert_ms.state == FatigueState.MICROSLEEP
    assert alert_ms.severity == AlertSeverity.CRITICAL
    assert alert_ms.haptic_alert_triggered is True

    # 3. Yawning and ocular drowsiness
    drowsy_fac = {"ear_mean": 0.18, "mar": 0.65, "blink_duration_ms": 450.0, "gaze_on_road": True}
    alert_dr = assess_driver_fatigue(drowsy_fac)
    assert alert_dr is not None
    assert alert_dr.state == FatigueState.DROWSY
    assert alert_dr.severity == AlertSeverity.HIGH

    # 4. Mobile phone distraction
    phone_fac = {"ear_mean": 0.28, "mar": 0.19, "phone_detected": True, "gaze_on_road": False}
    alert_ph = assess_driver_fatigue(phone_fac)
    assert alert_ph is not None
    assert alert_ph.state == FatigueState.DISTRACTED_PHONE
    assert alert_ph.severity == AlertSeverity.HIGH


def test_driver_safety_scorecard_and_rewards():
    """Tests multi-index driver scoring, tier classification, and insurance discount calculation."""
    # Scenario A: Smooth driving
    stream_smooth = get_trip_telemetry_stream("SCN-MUMBAI-SMOOTH", steps=15)
    score_smooth = calculate_driver_safety_score(stream_smooth)
    assert score_smooth.current_trip_score >= 90.0
    assert score_smooth.maruti_rewards_tier == "Diamond"
    assert score_smooth.insurance_premium_discount_pct == 20.0

    # Scenario B: Drowsy/Microsleep driving
    stream_drowsy = get_trip_telemetry_stream("SCN-EXPRESSWAY-DROWSY", steps=15)
    score_drowsy = calculate_driver_safety_score(stream_drowsy)
    assert score_drowsy.current_trip_score < score_smooth.current_trip_score
    assert score_drowsy.attentiveness_index < 75.0


def test_lane_discipline_and_echallan():
    """Tests computer vision lane boundary analysis and simulated e-Challan generation."""
    # 1. Improper lane change without indicator
    kinematics = {"speed_kmh": 68.0, "turn_indicator_active": False, "accel_lateral_g": 0.15}
    event = detect_lane_violation(kinematics=kinematics, lateral_offset_meters=0.95)
    assert event is not None
    assert event.violation_type == LaneViolationType.IMPROPER_LANE_CHANGE
    assert event.indicator_status is False

    challan = issue_educational_challan(event)
    assert challan.status == "ISSUED_EDUCATIONAL_FIRST_OFFENSE"
    assert challan.simulated_fine_inr == 500

    # 2. Stop line overrun at signal
    event_stop = detect_lane_violation(kinematics=kinematics, overrunning_stop_line=True)
    assert event_stop is not None
    assert event_stop.violation_type == LaneViolationType.STOP_LINE_OVERRUN


def test_traffic_signal_webster_optimization():
    """Tests Webster's minimum delay adaptive timing across congested arterial intersections."""
    junction = TrafficJunctionState(
        junction_id="JNC-TEST",
        junction_name="Test Flyover Crossroad",
        city="Mumbai",
        north_queue_pcu=220,
        south_queue_pcu=260,
        east_queue_pcu=90,
        west_queue_pcu=100,
        current_active_phase="NORTH_SOUTH",
        elapsed_green_seconds=30,
        current_cycle_seconds=130,
        congestion_level="CONGESTED",
    )

    plan = compute_adaptive_signal_plan(junction)
    assert 60 <= plan.computed_cycle_time_seconds <= 170
    assert plan.optimal_ns_green_seconds > plan.optimal_ew_green_seconds  # NS demand is much higher
    assert plan.estimated_delay_reduction_pct >= 25.0
    assert plan.fuel_saved_litres_per_hour > 0.0
    assert plan.co2_emissions_avoided_kg_per_hour > 0.0

    # Corridor-level optimization
    junctions = get_junction_network_state()
    corridor_opt = optimize_corridor_network(junctions)
    assert corridor_opt["junctions_optimized"] == 4
    assert corridor_opt["aggregate_metrics"]["avg_delay_reduction_pct"] >= 28.0


def test_v2x_alerts_and_geofencing():
    """Tests cellular V2X geofence proximity filtering."""
    # Distance calculation verification
    d = haversine_distance_meters(19.0620, 72.8530, 19.0607, 72.8524)
    assert 100.0 < d < 200.0

    # Retrieve active hazards
    alerts = get_relevant_v2x_alerts(vehicle_lat=19.0620, vehicle_lon=72.8530)
    assert len(alerts) >= 1
    # First hazard is the approaching ambulance within 600m
    amb_alert = [a for a in alerts if a["hazard_type"] == "EMERGENCY_VEHICLE_APPROACHING"][0]
    assert amb_alert["within_warning_zone"] is True
    assert amb_alert["distance_to_hazard_meters"] < 600.0
