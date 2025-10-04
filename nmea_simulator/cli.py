"""
Command-line interface for the NMEA simulator.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

from .server import NMEATCPServer, create_simulator_from_config
from .gps_tracker import RouteConfig, Waypoint


def create_default_config() -> Dict[str, Any]:
    """Create a default configuration."""
    return {
        "host": "0.0.0.0",
        "port": 10110,
        "speed_knots": 5.0,
        "route_type": "line",
        "start_lat": -33.8587,
        "start_lon": 151.2140,
        "end_lat": -33.8400,
        "end_lon": 151.2200,
        "center_lat": -33.8587,
        "center_lon": 151.2140,
        "radius_nm": 0.5,
        "num_points": 8,
        "width_nm": 0.3,
        "height_nm": 0.2,
    }


def save_config(config: Dict[str, Any], filepath: Path):
    """Save configuration to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(config, f, indent=2)


def load_config(filepath: Path) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def create_line_route_parser(subparsers):
    """Create parser for line route."""
    parser = subparsers.add_parser("line", help="Create a straight line route")
    parser.add_argument(
        "--start-lat", type=float, default=-33.8587, help="Start latitude"
    )
    parser.add_argument(
        "--start-lon", type=float, default=151.2140, help="Start longitude"
    )
    parser.add_argument("--end-lat", type=float, default=-33.8400, help="End latitude")
    parser.add_argument("--end-lon", type=float, default=151.2200, help="End longitude")
    parser.add_argument("--points", type=int, default=10, help="Number of waypoints")
    return parser


def create_circle_route_parser(subparsers):
    """Create parser for circular route."""
    parser = subparsers.add_parser("circle", help="Create a circular route")
    parser.add_argument(
        "--center-lat", type=float, default=-33.8587, help="Center latitude"
    )
    parser.add_argument(
        "--center-lon", type=float, default=151.2140, help="Center longitude"
    )
    parser.add_argument(
        "--radius", type=float, default=0.5, help="Radius in nautical miles"
    )
    parser.add_argument("--points", type=int, default=8, help="Number of waypoints")
    return parser


def create_rectangle_route_parser(subparsers):
    """Create parser for rectangular route."""
    parser = subparsers.add_parser("rectangle", help="Create a rectangular route")
    parser.add_argument(
        "--center-lat", type=float, default=-33.8587, help="Center latitude"
    )
    parser.add_argument(
        "--center-lon", type=float, default=151.2140, help="Center longitude"
    )
    parser.add_argument(
        "--width", type=float, default=0.3, help="Width in nautical miles"
    )
    parser.add_argument(
        "--height", type=float, default=0.2, help="Height in nautical miles"
    )
    return parser


def create_waypoint_route_parser(subparsers):
    """Create parser for custom waypoint route."""
    parser = subparsers.add_parser(
        "waypoints", help="Create a route from waypoints file"
    )
    parser.add_argument(
        "--file", type=Path, required=True, help="JSON file with waypoints"
    )
    return parser


async def run_simulator(config: Dict[str, Any]):
    """Run the NMEA simulator with the given configuration."""
    try:
        server = create_simulator_from_config(config)
        await server.start_server()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NMEA Simulator - TCP server that sends realistic NMEA messages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default line route
  nmea-simulator run

  # Run with custom configuration
  nmea-simulator run --host 127.0.0.1 --port 8080 --speed 10

  # Create a circular route
  nmea-simulator route circle --center-lat -33.8587 --center-lon 151.2140 --radius 1.0

  # Create a line route
  nmea-simulator route line --start-lat -33.8587 --start-lon 151.2140 --end-lat -33.8400 --end-lon 151.2200

  # Create a rectangular route
  nmea-simulator route rectangle --center-lat -33.8587 --center-lon 151.2140 --width 0.5 --height 0.3

  # Create route from waypoints file
  nmea-simulator route waypoints --file waypoints.json

  # Save configuration
  nmea-simulator config save --file config.json

  # Load and run with configuration
  nmea-simulator run --config config.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the NMEA simulator")
    run_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    run_parser.add_argument("--port", type=int, default=10110, help="Port to bind to")
    run_parser.add_argument("--speed", type=float, default=5.0, help="Speed in knots")
    run_parser.add_argument("--config", type=Path, help="Configuration file to load")

    # Route commands
    route_parser = subparsers.add_parser("route", help="Create route configurations")
    route_subparsers = route_parser.add_subparsers(dest="route_type", help="Route type")

    create_line_route_parser(route_subparsers)
    create_circle_route_parser(route_subparsers)
    create_rectangle_route_parser(route_subparsers)
    create_waypoint_route_parser(route_subparsers)

    # Config commands
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(
        dest="config_action", help="Config action"
    )

    save_parser = config_subparsers.add_parser(
        "save", help="Save current configuration"
    )
    save_parser.add_argument(
        "--file", type=Path, default=Path("config.json"), help="Output file"
    )

    load_parser = config_subparsers.add_parser("load", help="Load configuration")
    load_parser.add_argument("--file", type=Path, required=True, help="Input file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "run":
        if args.config:
            config = load_config(args.config)
        else:
            config = create_default_config()
            config["host"] = args.host
            config["port"] = args.port
            config["speed_knots"] = args.speed

        asyncio.run(run_simulator(config))

    elif args.command == "route":
        if args.route_type == "line":
            waypoints = RouteConfig.create_line_route(
                args.start_lat, args.start_lon, args.end_lat, args.end_lon, args.points
            )
            print(f"Created line route with {len(waypoints)} waypoints")
            for i, wp in enumerate(waypoints):
                print(f"  {i+1}: {wp.lat:.6f}, {wp.lon:.6f}")

        elif args.route_type == "circle":
            waypoints = RouteConfig.create_circular_route(
                args.center_lat, args.center_lon, args.radius, args.points
            )
            print(f"Created circular route with {len(waypoints)} waypoints")
            for i, wp in enumerate(waypoints):
                print(f"  {i+1}: {wp.lat:.6f}, {wp.lon:.6f}")

        elif args.route_type == "rectangle":
            waypoints = RouteConfig.create_rectangle_route(
                args.center_lat, args.center_lon, args.width, args.height
            )
            print(f"Created rectangular route with {len(waypoints)} waypoints")
            for i, wp in enumerate(waypoints):
                print(f"  {i+1}: {wp.lat:.6f}, {wp.lon:.6f}")

        elif args.route_type == "waypoints":
            with open(args.file, "r") as f:
                waypoint_data = json.load(f)
            waypoints = [
                Waypoint(wp["lat"], wp["lon"]) for wp in waypoint_data["waypoints"]
            ]
            print(f"Loaded {len(waypoints)} waypoints from {args.file}")
            for i, wp in enumerate(waypoints):
                print(f"  {i+1}: {wp.lat:.6f}, {wp.lon:.6f}")

    elif args.command == "config":
        if args.config_action == "save":
            config = create_default_config()
            save_config(config, args.file)
            print(f"Configuration saved to {args.file}")

        elif args.config_action == "load":
            config = load_config(args.file)
            print("Configuration loaded:")
            print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
