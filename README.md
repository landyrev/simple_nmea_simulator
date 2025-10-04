# NMEA Simulator

A TCP server that sends realistic NMEA messages with GPS route simulation. This tool simulates a boat's navigation system by generating NMEA 0183 messages with random variations and following configurable GPS routes.

## Features

- **Realistic NMEA Messages**: Generates all common NMEA sentence types (GPRMC, GPGGA, IIVHW, etc.)
- **Random Variations**: Adds realistic random variations to all values
- **GPS Route Simulation**: Follows configurable routes at specified speeds
- **Multiple Route Types**: Line, circle, rectangle, and custom waypoint routes
- **TCP Server**: Serves NMEA data to multiple clients simultaneously
- **CLI Interface**: Easy-to-use command-line interface with configuration options

## Installation

```bash
# Install in development mode
pip install -e .

# Or install from source
git clone <repository-url>
cd nmea_simulator
pip install -e .
```

## Usage

### Basic Usage

Run the simulator with default settings (Sydney Harbour line route at 5 knots):

```bash
nmea-simulator run
```

### Custom Configuration

```bash
# Run with custom host, port, and speed
nmea-simulator run --host 127.0.0.1 --port 8080 --speed 10

# Run with configuration file
nmea-simulator run --config my_config.json
```

### Route Types

#### Line Route
Create a straight line between two points:

```bash
nmea-simulator route line \
  --start-lat -33.8587 --start-lon 151.2140 \
  --end-lat -33.8400 --end-lon 151.2200 \
  --points 10
```

#### Circular Route
Create a circular route around a center point:

```bash
nmea-simulator route circle \
  --center-lat -33.8587 --center-lon 151.2140 \
  --radius 0.5 --points 8
```

#### Rectangular Route
Create a rectangular route:

```bash
nmea-simulator route rectangle \
  --center-lat -33.8587 --center-lon 151.2140 \
  --width 0.3 --height 0.2
```

#### Custom Waypoints
Create a route from a JSON file:

```bash
# Create waypoints.json
echo '{
  "waypoints": [
    {"lat": -33.8587, "lon": 151.2140},
    {"lat": -33.8600, "lon": 151.2200},
    {"lat": -33.8500, "lon": 151.2300}
  ]
}' > waypoints.json

nmea-simulator route waypoints --file waypoints.json
```

### Configuration Management

Save and load configurations:

```bash
# Save current configuration
nmea-simulator config save --file my_config.json

# Load configuration
nmea-simulator config load --file my_config.json
```

## NMEA Messages Generated

The simulator generates the following NMEA sentence types:

- **GPRMC**: Recommended minimum GPS data
- **GPGGA**: GPS fix data
- **GPGLL**: Geographic position
- **GPVTG**: Track made good and ground speed
- **GPGSA**: GPS DOP and active satellites
- **GPZDA**: Time and date
- **IIVHW**: Water speed and heading
- **IIHDT**: Heading
- **IIVBW**: Water referenced speed
- **WIMWD**: Wind direction and speed
- **WIMWV**: Wind speed and angle
- **IIMTW**: Water temperature
- **SDDPT**: Depth of water
- **SDDBT**: Depth below transducer
- **IIRPM**: Engine RPM
- **IIAPB**: Autopilot data
- **GPRMB**: Recommended minimum navigation
- **AIVDO/AIVDM**: AIS vessel data

## Configuration File Format

```json
{
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
  "height_nm": 0.2
}
```

## Connecting to the Simulator

The simulator runs a TCP server that sends NMEA messages every second. You can connect to it using any TCP client:

```bash
# Using netcat
nc localhost 10110

# Using telnet
telnet localhost 10110

# Using Python
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 10110))
while True:
    data = s.recv(1024)
    print(data.decode())
```

## Example Output

```
$GPRMC,083430.963,A,3459.838138,S,13830.037754,E,4.7,7.6,041025,,,*3B
$IIVHW,7.6,T,7.6,M,4.7,N,8.7,K*59
$GPVTG,7.6,T,7.6,M,4.7,N,8.7,K*42
$IIHDT,7.6,T*23
$GPGLL,3459.838138,S,13830.037754,E,083430.963,A*20
$GPGGA,083430.963,3459.838138,S,13830.037754,E,1,4,1.0,2.0,M,,,,*2C
...
```

## Development

### Running Tests

```bash
python -m pytest
```

### Code Style

```bash
black nmea_simulator/
flake8 nmea_simulator/
```

## License

MIT License - see LICENSE file for details.
