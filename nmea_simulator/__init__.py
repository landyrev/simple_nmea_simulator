"""
NMEA Simulator - A TCP server that sends realistic NMEA messages.

This package provides a comprehensive NMEA message simulator that can:
- Generate realistic NMEA messages with random variations
- Follow configurable GPS routes at specified speeds
- Serve NMEA data over TCP to multiple clients
- Support various route types (line, circle, rectangle, custom waypoints)
"""

__version__ = "0.1.0"
__author__ = "Alexey Landyrev"

from .server import NMEATCPServer, NMEASimulator
from .gps_tracker import GPSTracker, Waypoint, RouteConfig
from .messages import Position

__all__ = [
    "NMEATCPServer",
    "NMEASimulator",
    "GPSTracker",
    "Waypoint",
    "RouteConfig",
    "Position",
]
