"""
GPS position tracking along a line with configurable speed.
"""

import math
import time
from typing import List, Tuple, Optional
from dataclasses import dataclass
from .messages import Position


@dataclass
class Waypoint:
    """A waypoint with latitude and longitude."""

    lat: float
    lon: float

    def distance_to(self, other: "Waypoint") -> float:
        """Calculate distance to another waypoint in meters using Haversine formula."""
        R = 6371000  # Earth's radius in meters

        lat1_rad = math.radians(self.lat)
        lat2_rad = math.radians(other.lat)
        delta_lat = math.radians(other.lat - self.lat)
        delta_lon = math.radians(other.lon - self.lon)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def bearing_to(self, other: "Waypoint") -> float:
        """Calculate bearing to another waypoint in degrees."""
        lat1_rad = math.radians(self.lat)
        lat2_rad = math.radians(other.lat)
        delta_lon_rad = math.radians(other.lon - self.lon)

        y = math.sin(delta_lon_rad) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(
            lat2_rad
        ) * math.cos(delta_lon_rad)

        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)

        return (bearing_deg + 360) % 360


class GPSTracker:
    """GPS position tracker that follows a route at a given speed."""

    def __init__(self, waypoints: List[Waypoint], speed_knots: float = 5.0):
        """
        Initialize GPS tracker.

        Args:
            waypoints: List of waypoints to follow
            speed_knots: Speed in knots
        """
        if len(waypoints) < 2:
            raise ValueError("At least 2 waypoints are required")

        self.waypoints = waypoints
        self.speed_knots = speed_knots
        self.speed_ms = speed_knots * 0.514444  # Convert knots to m/s

        self.current_waypoint_index = 0
        self.start_time = time.time()
        self.total_distance = self._calculate_total_distance()
        self.current_position = Position(waypoints[0].lat, waypoints[0].lon)

    def _calculate_total_distance(self) -> float:
        """Calculate total distance of the route."""
        total_distance = 0.0
        for i in range(len(self.waypoints) - 1):
            total_distance += self.waypoints[i].distance_to(self.waypoints[i + 1])

        # For circular routes, add distance from last waypoint back to first
        if len(self.waypoints) > 2:
            total_distance += self.waypoints[-1].distance_to(self.waypoints[0])

        return total_distance

    def get_current_position(self) -> Position:
        """Get current position based on elapsed time and speed."""
        elapsed_time = time.time() - self.start_time
        distance_traveled = elapsed_time * self.speed_ms

        # Handle circular route by using modulo
        if distance_traveled >= self.total_distance:
            # For circular routes, wrap around
            distance_traveled = distance_traveled % self.total_distance

        # Find current segment
        current_distance = 0.0
        segment_start = self.waypoints[0]

        for i in range(len(self.waypoints)):
            # For circular routes, the last segment goes back to the first waypoint
            if i == len(self.waypoints) - 1:
                segment_end = self.waypoints[0]  # Back to start for circular route
            else:
                segment_end = self.waypoints[i + 1]

            segment_distance = segment_start.distance_to(segment_end)

            if distance_traveled < current_distance + segment_distance:
                # We're in this segment
                segment_progress = (
                    distance_traveled - current_distance
                ) / segment_distance
                # Update current waypoint index for heading calculation
                self.current_waypoint_index = i
                return self._interpolate_position(
                    segment_start, segment_end, segment_progress
                )

            current_distance += segment_distance
            segment_start = segment_end

        # If we've passed all waypoints, return the last one
        self.current_waypoint_index = len(self.waypoints) - 2
        return Position(self.waypoints[-1].lat, self.waypoints[-1].lon)

    def _interpolate_position(
        self, start: Waypoint, end: Waypoint, progress: float
    ) -> Position:
        """Interpolate position between two waypoints."""
        # Clamp progress between 0 and 1
        progress = max(0.0, min(1.0, progress))

        lat = start.lat + (end.lat - start.lat) * progress
        lon = start.lon + (end.lon - start.lon) * progress

        return Position(lat, lon)

    def get_current_heading(self) -> float:
        """Get current heading based on current segment."""
        if self.current_waypoint_index >= len(self.waypoints) - 1:
            # Use bearing from second-to-last to last waypoint
            if len(self.waypoints) >= 2:
                return self.waypoints[-2].bearing_to(self.waypoints[-1])
            return 0.0

        current_wp = self.waypoints[self.current_waypoint_index]
        next_wp = self.waypoints[self.current_waypoint_index + 1]
        return current_wp.bearing_to(next_wp)

    def get_current_speed(self) -> float:
        """Get current speed in knots."""
        return self.speed_knots

    def is_route_complete(self) -> bool:
        """Check if the route has been completed."""
        elapsed_time = time.time() - self.start_time
        expected_time = self.total_distance / self.speed_ms
        return elapsed_time >= expected_time

    def reset_route(self):
        """Reset the route to start from the beginning."""
        self.start_time = time.time()
        self.current_waypoint_index = 0
        self.current_position = Position(self.waypoints[0].lat, self.waypoints[0].lon)


class RouteConfig:
    """Configuration for GPS routes."""

    @staticmethod
    def create_circular_route(
        center_lat: float, center_lon: float, radius_nm: float, num_points: int = 8
    ) -> List[Waypoint]:
        """Create a circular route around a center point."""
        waypoints = []
        # Convert nautical miles to degrees
        # 1 nautical mile = 1/60 degree of latitude
        # For longitude, we need to account for latitude
        radius_lat_deg = radius_nm / 60.0
        radius_lon_deg = radius_nm / (60.0 * math.cos(math.radians(center_lat)))

        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            lat = center_lat + radius_lat_deg * math.cos(angle)
            lon = center_lon + radius_lon_deg * math.sin(angle)
            waypoints.append(Waypoint(lat, lon))

        return waypoints

    @staticmethod
    def create_line_route(
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        num_points: int = 10,
    ) -> List[Waypoint]:
        """Create a straight line route between two points."""
        waypoints = []

        for i in range(num_points):
            progress = i / (num_points - 1)
            lat = start_lat + (end_lat - start_lat) * progress
            lon = start_lon + (end_lon - start_lon) * progress
            waypoints.append(Waypoint(lat, lon))

        return waypoints

    @staticmethod
    def create_rectangle_route(
        center_lat: float, center_lon: float, width_nm: float, height_nm: float
    ) -> List[Waypoint]:
        """Create a rectangular route."""
        width_deg = width_nm / 60.0
        height_deg = height_nm / 60.0

        waypoints = [
            Waypoint(center_lat - height_deg / 2, center_lon - width_deg / 2),  # SW
            Waypoint(center_lat - height_deg / 2, center_lon + width_deg / 2),  # SE
            Waypoint(center_lat + height_deg / 2, center_lon + width_deg / 2),  # NE
            Waypoint(center_lat + height_deg / 2, center_lon - width_deg / 2),  # NW
            Waypoint(
                center_lat - height_deg / 2, center_lon - width_deg / 2
            ),  # Back to start
        ]

        return waypoints
