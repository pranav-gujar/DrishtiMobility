"""
Computer Vision Lane Discipline & Automated Violation Detection Engine.
Monitors lane boundaries, improper overtakes, solid line crossings, and
generates simulated educational e-Challans for driver behavior correction.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.schemas.mobility import (
    LaneDepartureEvent,
    ViolationChallanRecord,
    LaneViolationType,
    AlertSeverity,
)

# Indian Road Standards (IRC: SP:99-2013)
LANE_WIDTH_METERS = 3.5
LATERAL_DRIFT_THRESHOLD_METERS = 0.75


def detect_lane_violation(
    kinematics: Dict[str, Any],
    lateral_offset_meters: float = 0.20,
    crossing_solid_line: bool = False,
    overrunning_stop_line: bool = False,
    speed_limit_kmh: float = 80.0,
) -> Optional[LaneDepartureEvent]:
    """
    Evaluates vehicle lateral movement against lane markings and turn signal status.
    """
    speed_kmh = float(kinematics.get("speed_kmh", 50.0))
    indicator = bool(kinematics.get("turn_indicator_active", False))
    lat_g = abs(float(kinematics.get("accel_lateral_g", 0.0)))

    event_id = f"LNE-{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    # 1. Stop Line Overrun at Intersection
    if overrunning_stop_line:
        return LaneDepartureEvent(
            event_id=event_id,
            violation_type=LaneViolationType.STOP_LINE_OVERRUN,
            severity=AlertSeverity.HIGH,
            vehicle_speed_kmh=speed_kmh,
            lateral_displacement_meters=0.0,
            indicator_status=indicator,
            camera_confidence_score=0.96,
            intervention_recommended="Stop line encroached on red signal. Halt before the pedestrian zebra corridor.",
        )

    # 2. Aggressive Reckless Weaving (high lateral G + rapid drift)
    if lat_g >= 0.40 and abs(lateral_offset_meters) >= 0.90:
        return LaneDepartureEvent(
            event_id=event_id,
            violation_type=LaneViolationType.RECKLESS_WEAVING,
            severity=AlertSeverity.CRITICAL,
            vehicle_speed_kmh=speed_kmh,
            lateral_displacement_meters=round(lateral_offset_meters, 2),
            indicator_status=indicator,
            camera_confidence_score=0.94,
            intervention_recommended="Aggressive slalom/weaving detected. Maintain steady lane centering to avoid side-swipe collision.",
        )

    # 3. Solid Line Crossing (e.g. flyover ramp, bridge, or tunnel)
    if crossing_solid_line:
        return LaneDepartureEvent(
            event_id=event_id,
            violation_type=LaneViolationType.SOLID_LINE_CROSSING,
            severity=AlertSeverity.MEDIUM,
            vehicle_speed_kmh=speed_kmh,
            lateral_displacement_meters=round(lateral_offset_meters, 2),
            indicator_status=indicator,
            camera_confidence_score=0.95,
            intervention_recommended="Overtaking prohibited on continuous solid lane marking per IRC safety rules.",
        )

    # 4. Improper Lane Change (lane shift without turn indicator)
    if abs(lateral_offset_meters) >= LATERAL_DRIFT_THRESHOLD_METERS and not indicator:
        return LaneDepartureEvent(
            event_id=event_id,
            violation_type=LaneViolationType.IMPROPER_LANE_CHANGE,
            severity=AlertSeverity.LOW if speed_kmh < 40.0 else AlertSeverity.MEDIUM,
            vehicle_speed_kmh=speed_kmh,
            lateral_displacement_meters=round(lateral_offset_meters, 2),
            indicator_status=indicator,
            camera_confidence_score=0.92,
            intervention_recommended="Always indicate at least 3 seconds prior to changing lanes to alert trailing vehicles.",
        )

    # 5. Speeding
    if speed_kmh > speed_limit_kmh + 10.0:
        return LaneDepartureEvent(
            event_id=event_id,
            violation_type=LaneViolationType.ZONED_SPEED_LIMIT_EXCEEDED,
            severity=AlertSeverity.HIGH,
            vehicle_speed_kmh=speed_kmh,
            lateral_displacement_meters=0.0,
            indicator_status=indicator,
            camera_confidence_score=0.98,
            intervention_recommended=f"Speed limit ({speed_limit_kmh:.0f} km/h) exceeded. Reduce velocity to match road conditions.",
        )

    return None


def issue_educational_challan(
    event: LaneDepartureEvent,
    vehicle_vin: str = "MA3EWE21S0019284",
    license_plate: str = "MH 02 FP 4821",
) -> ViolationChallanRecord:
    """
    Generates a simulated digital e-Challan with a coaching-first philosophy
    (waives fine for first-time educational offenders).
    """
    fine_map = {
        LaneViolationType.IMPROPER_LANE_CHANGE: 500,
        LaneViolationType.SOLID_LINE_CROSSING: 1000,
        LaneViolationType.STOP_LINE_OVERRUN: 1000,
        LaneViolationType.ZONED_SPEED_LIMIT_EXCEEDED: 2000,
        LaneViolationType.RECKLESS_WEAVING: 5000,
    }

    challan_id = f"CHL-MSIL-{int(datetime.now(timezone.utc).timestamp())}"
    return ViolationChallanRecord(
        challan_id=challan_id,
        vehicle_vin=vehicle_vin,
        license_plate=license_plate,
        violation=event.violation_type,
        speed_detected_kmh=event.vehicle_speed_kmh,
        speed_limit_kmh=80.0,
        simulated_fine_inr=fine_map.get(event.violation_type, 1000),
        evidence_frame_uri=f"/static/evidence/{challan_id}.jpg",
        status="ISSUED_EDUCATIONAL_FIRST_OFFENSE",
    )
