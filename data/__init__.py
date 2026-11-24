"""Synthetic telematics and urban traffic scenarios for DrishtiMobility."""
from data.synthetic_telematics import (
    TRIP_SCENARIOS,
    CORRIDOR_JUNCTIONS,
    get_trip_telemetry_stream,
    get_junction_network_state,
)

__all__ = [
    "TRIP_SCENARIOS",
    "CORRIDOR_JUNCTIONS",
    "get_trip_telemetry_stream",
    "get_junction_network_state",
]
