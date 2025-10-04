"""
TCP server for sending NMEA messages.
"""

import asyncio
import socket
import time
import random
from typing import List, Optional
from .messages import (
    GPRMC,
    IIVHW,
    GPVTG,
    IIHDT,
    GPGLL,
    GPGGA,
    GPGSA,
    GPZDA,
    IIVBW,
    WIMWD,
    WIMWV,
    IIMTW,
    SDDPT,
    SDDBT,
    IIRPM,
    IIAPB,
    GPRMB,
    AIVDO,
    AIVDM,
)
from .gps_tracker import GPSTracker, Waypoint, RouteConfig


class NMEASimulator:
    """NMEA message simulator that generates realistic NMEA data."""

    def __init__(self, gps_tracker: GPSTracker):
        self.gps_tracker = gps_tracker
        self.engine_rpm = 612.0
        self.engine_pitch = 10.5
        self.wind_direction = 255.1
        self.wind_speed = 27.8
        self.water_temp = 6.7
        self.depth = 2.2
        self.ais_payloads = [
            "17PaewhP0gar0FkcvG4hBh>t0000",
            "57Paewh00001<To7;?@plD5<Tl0000000000000U1@:552R8R2TnA3QF",
            "@00000000000002",
        ]

    def generate_messages(self) -> List[str]:
        """Generate a complete set of NMEA messages for current position."""
        position = self.gps_tracker.get_current_position()
        heading = self.gps_tracker.get_current_heading()
        speed = self.gps_tracker.get_current_speed()

        # Add some variation to environmental data
        self._update_environmental_data()

        messages = []

        # Core GPS messages
        messages.append(GPRMC(position, speed, heading).to_string())
        messages.append(IIVHW(speed, heading).to_string())
        messages.append(GPVTG(heading, speed).to_string())
        messages.append(IIHDT(heading).to_string())
        messages.append(GPGLL(position).to_string())
        messages.append(
            GPGGA(position, satellites=4, hdop=1.0, altitude=2.0).to_string()
        )
        messages.append(
            GPGSA([8, 11, 15, 22], pdop=2.0, hdop=1.0, vdop=1.0).to_string()
        )
        messages.append(GPZDA().to_string())

        # Water speed and direction
        messages.append(IIVBW(speed).to_string())

        # Wind data
        messages.append(WIMWD(self.wind_direction, self.wind_speed).to_string())
        messages.append(WIMWV(self.wind_direction, self.wind_speed).to_string())

        # Water temperature
        messages.append(IIMTW(self.water_temp).to_string())

        # Depth data
        messages.append(SDDPT(self.depth, 0.3).to_string())
        messages.append(
            SDDBT(self.depth * 3.28084, self.depth, self.depth * 0.546807).to_string()
        )

        # Engine data
        messages.append(IIRPM("1", self.engine_rpm, self.engine_pitch).to_string())
        messages.append(IIRPM("2", 0, self.engine_pitch).to_string())

        # Navigation data
        messages.append(IIAPB(0.012140, 260.4, heading).to_string())
        messages.append(GPRMB(position, 0.012140, 3.573, speed, heading).to_string())

        # AIS messages
        messages.append(AIVDO(1, 1, 1, "A", self.ais_payloads[0]).to_string())
        messages.append(AIVDM(1, 1, 1, "A", self.ais_payloads[0]).to_string())
        messages.append(AIVDO(2, 1, 9, "A", self.ais_payloads[1]).to_string())
        messages.append(AIVDO(2, 2, 9, "A", self.ais_payloads[2]).to_string())
        messages.append(AIVDM(2, 1, 9, "A", self.ais_payloads[1]).to_string())
        messages.append(AIVDM(2, 2, 9, "A", self.ais_payloads[2]).to_string())

        return messages

    def _update_environmental_data(self):
        """Update environmental data with small random variations."""
        # Wind direction and speed variation
        self.wind_direction = (self.wind_direction + random.uniform(-2, 2)) % 360
        self.wind_speed = max(0, self.wind_speed + random.uniform(-1, 1))

        # Water temperature variation
        self.water_temp = max(0, self.water_temp + random.uniform(-0.2, 0.2))

        # Depth variation
        self.depth = max(0.1, self.depth + random.uniform(-0.1, 0.1))

        # Engine RPM variation
        self.engine_rpm = max(0, self.engine_rpm + random.uniform(-5, 5))
        self.engine_pitch = max(0, self.engine_pitch + random.uniform(-0.5, 0.5))


class NMEATCPServer:
    """TCP server that sends NMEA messages to connected clients."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 10110,
        gps_tracker: Optional[GPSTracker] = None,
    ):
        self.host = host
        self.port = port
        self.gps_tracker = gps_tracker or self._create_default_tracker()
        self.simulator = NMEASimulator(self.gps_tracker)
        self.clients = set()
        self.running = False

    def _create_default_tracker(self) -> GPSTracker:
        """Create a default GPS tracker with a simple route."""
        # Default route: Sydney Harbour area
        waypoints = [
            Waypoint(-33.8587, 151.2140),  # Sydney Opera House
            Waypoint(-33.8600, 151.2200),  # Harbour Bridge
            Waypoint(-33.8500, 151.2300),  # North of harbour
            Waypoint(-33.8400, 151.2200),  # Back towards city
        ]
        return GPSTracker(waypoints, speed_knots=5.0)

    async def start_server(self):
        """Start the TCP server."""
        server = await asyncio.start_server(self.handle_client, self.host, self.port)

        print(f"NMEA Simulator TCP server started on {self.host}:{self.port}")
        print(
            f"Route: {len(self.gps_tracker.waypoints)} waypoints, {self.gps_tracker.speed_knots} knots"
        )
        print("Press Ctrl+C to stop")

        self.running = True

        try:
            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            self.running = False

    async def handle_client(self, reader, writer):
        """Handle a new client connection."""
        client_addr = writer.get_extra_info("peername")
        print(f"Client connected: {client_addr}")

        self.clients.add(writer)

        try:
            while self.running:
                # Generate NMEA messages
                messages = self.simulator.generate_messages()

                # Send all messages to this client
                for message in messages:
                    data = (message + "\r\n").encode("utf-8")
                    writer.write(data)

                await writer.drain()
                await asyncio.sleep(1.0)  # Send every second

        except ConnectionResetError:
            print(f"Client disconnected: {client_addr}")
        except Exception as e:
            print(f"Error with client {client_addr}: {e}")
        finally:
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()

    def stop_server(self):
        """Stop the server."""
        self.running = False
        for client in self.clients:
            client.close()


def create_simulator_from_config(config: dict) -> NMEATCPServer:
    """Create a simulator from configuration dictionary."""
    # Extract configuration
    host = config.get("host", "0.0.0.0")
    port = config.get("port", 10110)
    speed_knots = config.get("speed_knots", 5.0)
    route_type = config.get("route_type", "line")

    # Create waypoints based on route type
    if route_type == "line":
        start_lat = config.get("start_lat", -33.8587)
        start_lon = config.get("start_lon", 151.2140)
        end_lat = config.get("end_lat", -33.8400)
        end_lon = config.get("end_lon", 151.2200)
        waypoints = RouteConfig.create_line_route(
            start_lat, start_lon, end_lat, end_lon
        )

    elif route_type == "circle":
        center_lat = config.get("center_lat", -33.8587)
        center_lon = config.get("center_lon", 151.2140)
        radius_nm = config.get("radius_nm", 0.5)
        num_points = config.get("num_points", 8)
        waypoints = RouteConfig.create_circular_route(
            center_lat, center_lon, radius_nm, num_points
        )

    elif route_type == "rectangle":
        center_lat = config.get("center_lat", -33.8587)
        center_lon = config.get("center_lon", 151.2140)
        width_nm = config.get("width_nm", 0.3)
        height_nm = config.get("height_nm", 0.2)
        waypoints = RouteConfig.create_rectangle_route(
            center_lat, center_lon, width_nm, height_nm
        )

    else:
        raise ValueError(f"Unknown route type: {route_type}")

    gps_tracker = GPSTracker(waypoints, speed_knots)
    return NMEATCPServer(host, port, gps_tracker)
