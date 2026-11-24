"""
Pydantic schemas for DrishtiMobility.
Covers Driver In-Cabin Monitoring, Vehicle Kinematics, Lane Discipline,
Adaptive Traffic Junctions, and V2X Hazard Dissemination.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FatigueState(str, Enum):
    ATTENTIVE = "ATTENTIVE"
    MILD_FATIGUE = "MILD_FATIGUE"
    DROWSY = "DROWSY"
    MICROSLEEP = "MICROSLEEP"
    DISTRACTED_PHONE = "DISTRACTED_PHONE"
    DISTRACTED_GAZE = "DISTRACTED_GAZE"


class LaneViolationType(str, Enum):
    IMPROPER_LANE_CHANGE = "IMPROPER_LANE_CHANGE"
    SOLID_LINE_CROSSING = "SOLID_LINE_CROSSING"
    ZONED_SPEED_LIMIT_EXCEEDED = "ZONED_SPEED_LIMIT_EXCEEDED"
    STOP_LINE_OVERRUN = "STOP_LINE_OVERRUN"
    RECKLESS_WEAVING = "RECKLESS_WEAVING"


class DriverFacialTelemetry(BaseModel):
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ear_left: float = Field(..., ge=0.0, le=0.6, description="Eye Aspect Ratio Left")
    ear_right: float = Field(..., ge=0.0, le=0.6, description="Eye Aspect Ratio Right")
    ear_mean: float = Field(..., ge=0.0, le=0.6, description="Mean Eye Aspect Ratio")
    mar: float = Field(..., ge=0.0, le=1.5, description="Mouth Aspect Ratio (Yawning index)")
    head_yaw_deg: float = Field(..., ge=-90.0, le=90.0, description="Head rotation yaw (left/right)")
    head_pitch_deg: float = Field(..., ge=-90.0, le=90.0, description="Head tilt pitch (down/up)")
    blink_duration_ms: float = Field(..., ge=0.0, description="Eye closure duration in ms")
    phone_detected: bool = Field(default=False, description="Mobile device in driver hand/lap")
    gaze_on_road: bool = Field(default=True, description="True if forward road cone gaze")


class VehicleKinematics(BaseModel):
    speed_kmh: float = Field(..., ge=0.0, le=250.0)
    accel_lateral_g: float = Field(..., ge=-2.0, le=2.0, description="Centrifugal turning Gs")
    accel_longitudinal_g: float = Field(..., ge=-2.0, le=2.0, description="Braking (-) or acceleration (+)")
    steering_angle_deg: float = Field(..., ge=-540.0, le=540.0)
    turn_indicator_active: bool = Field(default=False)
    seatbelt_latched: bool = Field(default=True)
    odometer_km: float = Field(..., ge=0.0)
    fuel_efficiency_kmpl: float = Field(default=18.5, ge=0.0)


class DriverFatigueAlert(BaseModel):
    alert_id: str
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state: FatigueState
    severity: AlertSeverity
    trigger_reason: str
    ear_value: float
    mar_value: float
    duration_seconds: float
    haptic_alert_triggered: bool = True
    audio_chime_triggered: bool = True
    suggested_coaching: str


class DriverSafetyScorecard(BaseModel):
    driver_id: str = "DRV-IN-9842"
    vehicle_vin: str = "MA3EWE21S0019284"
    model_name: str = "Maruti Suzuki Grand Vitara Intelligent Hybrid"
    current_trip_score: float = Field(..., ge=0.0, le=100.0)
    lifetime_safety_score: float = Field(..., ge=0.0, le=100.0)
    smooth_driving_index: float = Field(..., ge=0.0, le=100.0)
    attentiveness_index: float = Field(..., ge=0.0, le=100.0)
    speed_compliance_index: float = Field(..., ge=0.0, le=100.0)
    harsh_braking_events_per_100km: float = 0.0
    harsh_acceleration_events_per_100km: float = 0.0
    mobile_distraction_seconds: float = 0.0
    maruti_rewards_tier: str = Field(default="Platinum", description="Silver, Gold, Platinum, Diamond")
    insurance_premium_discount_pct: float = Field(default=15.0, ge=0.0, le=30.0)
    safe_km_streak: int = 1420


class LaneDepartureEvent(BaseModel):
    event_id: str
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    violation_type: LaneViolationType
    severity: AlertSeverity
    vehicle_speed_kmh: float
    lateral_displacement_meters: float
    indicator_status: bool
    camera_confidence_score: float = Field(..., ge=0.0, le=1.0)
    intervention_recommended: str


class TrafficJunctionState(BaseModel):
    junction_id: str
    junction_name: str
    city: str = "Mumbai"
    corridor_name: str = "Western Express Highway (WEH) Corridor"
    north_queue_pcu: int = Field(..., ge=0, description="Passenger Car Units")
    south_queue_pcu: int = Field(..., ge=0)
    east_queue_pcu: int = Field(..., ge=0)
    west_queue_pcu: int = Field(..., ge=0)
    current_active_phase: str = Field(..., description="NORTH_SOUTH or EAST_WEST")
    elapsed_green_seconds: int = Field(..., ge=0)
    current_cycle_seconds: int = Field(default=120)
    congestion_level: str = "MODERATE"  # FREE_FLOW, MODERATE, CONGESTED, GRIDLOCK


class AdaptiveSignalPlan(BaseModel):
    junction_id: str
    computed_cycle_time_seconds: int
    optimal_ns_green_seconds: int
    optimal_ew_green_seconds: int
    amber_seconds: int = 4
    all_red_seconds: int = 2
    estimated_delay_reduction_pct: float
    webster_critical_flow_ratio: float
    fuel_saved_litres_per_hour: float
    co2_emissions_avoided_kg_per_hour: float


class V2XAlertBroadcast(BaseModel):
    broadcast_id: str
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hazard_type: str = "EMERGENCY_VEHICLE_APPROACHING"
    origin_latitude: float = 19.1136
    origin_longitude: float = 72.8697
    relevance_radius_meters: float = 500.0
    heading_degrees: float = 180.0
    message_text: str
    recommended_driver_action: str
    active: bool = True


class ViolationChallanRecord(BaseModel):
    challan_id: str
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    vehicle_vin: str
    license_plate: str
    violation: LaneViolationType
    speed_detected_kmh: float
    speed_limit_kmh: float
    simulated_fine_inr: int
    evidence_frame_uri: str
    status: str = "ISSUED_EDUCATIONAL_FIRST_OFFENSE"
