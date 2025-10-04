"""
NMEA message parsing and generation utilities.
"""

import random
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Position:
    """GPS position with latitude and longitude."""

    lat: float
    lon: float

    def to_nmea_lat(self) -> Tuple[str, str]:
        """Convert latitude to NMEA format (DDMM.MMMMMM, N/S)."""
        abs_lat = abs(self.lat)
        degrees = int(abs_lat)
        minutes = (abs_lat - degrees) * 60
        direction = "N" if self.lat >= 0 else "S"
        return f"{degrees:02d}{minutes:09.6f}", direction

    def to_nmea_lon(self) -> Tuple[str, str]:
        """Convert longitude to NMEA format (DDDMM.MMMMMM, E/W)."""
        abs_lon = abs(self.lon)
        degrees = int(abs_lon)
        minutes = (abs_lon - degrees) * 60
        direction = "E" if self.lon >= 0 else "W"
        return f"{degrees:03d}{minutes:09.6f}", direction


class NMEAMessage:
    """Base class for NMEA messages."""

    def __init__(self, sentence_type: str):
        self.sentence_type = sentence_type
        self.timestamp = datetime.now(timezone.utc)

    def calculate_checksum(self, data: str) -> str:
        """Calculate NMEA checksum."""
        checksum = 0
        for char in data:
            checksum ^= ord(char)
        return f"{checksum:02X}"

    def add_random_variation(
        self, value: float, variation_percent: float = 0.1
    ) -> float:
        """Add random variation to a value."""
        variation = value * variation_percent * (random.random() - 0.5) * 2
        return value + variation

    def format_time(self) -> str:
        """Format current time as HHMMSS.SSS."""
        return self.timestamp.strftime("%H%M%S.%f")[:-3]

    def to_string(self) -> str:
        """Convert message to NMEA string. Override in subclasses."""
        raise NotImplementedError


class GPRMC(NMEAMessage):
    """GPS Recommended Minimum sentence."""

    def __init__(self, position: Position, speed_knots: float, course: float):
        super().__init__("GPRMC")
        self.position = position
        self.speed_knots = speed_knots
        self.course = course

    def to_string(self) -> str:
        lat_str, lat_dir = self.position.to_nmea_lat()
        lon_str, lon_dir = self.position.to_nmea_lon()

        # Add random variations
        speed = self.add_random_variation(self.speed_knots, 0.05)
        course = self.add_random_variation(self.course, 0.1)

        data = f"$GPRMC,{self.format_time()},A,{lat_str},{lat_dir},{lon_str},{lon_dir},{speed:.1f},{course:.1f},{self.timestamp.strftime('%d%m%y')},,,*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class IIVHW(NMEAMessage):
    """Water speed and heading."""

    def __init__(self, speed_knots: float, heading: float):
        super().__init__("IIVHW")
        self.speed_knots = speed_knots
        self.heading = heading

    def to_string(self) -> str:
        speed = self.add_random_variation(self.speed_knots, 0.05)
        heading = self.add_random_variation(self.heading, 0.1)
        speed_kmh = speed * 1.852

        data = (
            f"$IIVHW,{heading:.1f},T,{heading:.1f},M,{speed:.1f},N,{speed_kmh:.1f},K*"
        )
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class GPVTG(NMEAMessage):
    """Track made good and ground speed."""

    def __init__(self, course: float, speed_knots: float):
        super().__init__("GPVTG")
        self.course = course
        self.speed_knots = speed_knots

    def to_string(self) -> str:
        course = self.add_random_variation(self.course, 0.1)
        speed = self.add_random_variation(self.speed_knots, 0.05)
        speed_kmh = speed * 1.852

        data = f"$GPVTG,{course:.1f},T,{course:.1f},M,{speed:.1f},N,{speed_kmh:.1f},K*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class IIHDT(NMEAMessage):
    """Heading."""

    def __init__(self, heading: float):
        super().__init__("IIHDT")
        self.heading = heading

    def to_string(self) -> str:
        heading = self.add_random_variation(self.heading, 0.1)
        data = f"$IIHDT,{heading:.1f},T*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class GPGLL(NMEAMessage):
    """Geographic position - latitude/longitude."""

    def __init__(self, position: Position):
        super().__init__("GPGLL")
        self.position = position

    def to_string(self) -> str:
        lat_str, lat_dir = self.position.to_nmea_lat()
        lon_str, lon_dir = self.position.to_nmea_lon()

        data = f"$GPGLL,{lat_str},{lat_dir},{lon_str},{lon_dir},{self.format_time()},A*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class GPGGA(NMEAMessage):
    """Global positioning system fix data."""

    def __init__(
        self,
        position: Position,
        quality: int = 1,
        satellites: int = 4,
        hdop: float = 1.0,
        altitude: float = 2.0,
    ):
        super().__init__("GPGGA")
        self.position = position
        self.quality = quality
        self.satellites = satellites
        self.hdop = hdop
        self.altitude = altitude

    def to_string(self) -> str:
        lat_str, lat_dir = self.position.to_nmea_lat()
        lon_str, lon_dir = self.position.to_nmea_lon()

        # Add random variations
        satellites = max(1, int(self.add_random_variation(self.satellites, 0.2)))
        hdop = max(0.5, self.add_random_variation(self.hdop, 0.3))
        altitude = self.add_random_variation(self.altitude, 0.1)

        data = f"$GPGGA,{self.format_time()},{lat_str},{lat_dir},{lon_str},{lon_dir},{self.quality},{satellites},{hdop:.1f},{altitude:.1f},M,,,,*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class GPGSA(NMEAMessage):
    """GPS DOP and active satellites."""

    def __init__(
        self,
        satellites: List[int],
        pdop: float = 2.0,
        hdop: float = 1.0,
        vdop: float = 1.0,
    ):
        super().__init__("GPGSA")
        self.satellites = satellites
        self.pdop = pdop
        self.hdop = hdop
        self.vdop = vdop

    def to_string(self) -> str:
        # Add random variations
        pdop = max(0.5, self.add_random_variation(self.pdop, 0.2))
        hdop = max(0.5, self.add_random_variation(self.hdop, 0.2))
        vdop = max(0.5, self.add_random_variation(self.vdop, 0.2))

        sat_list = ",".join(
            [str(sat) if sat in self.satellites else "" for sat in range(1, 13)]
        )
        data = f"$GPGSA,A,3,{sat_list},{pdop:.1f},{hdop:.1f},{vdop:.1f}*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class GPZDA(NMEAMessage):
    """Time and date."""

    def __init__(self):
        super().__init__("GPZDA")

    def to_string(self) -> str:
        data = (
            f"$GPZDA,{self.format_time()},{self.timestamp.strftime('%d,%m,%Y')},02,00*"
        )
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class IIVBW(NMEAMessage):
    """Water referenced speed and direction."""

    def __init__(self, speed_knots: float):
        super().__init__("IIVBW")
        self.speed_knots = speed_knots

    def to_string(self) -> str:
        speed = self.add_random_variation(self.speed_knots, 0.05)
        data = f"$IIVBW,{speed:.1f},{speed:.1f},A,{speed*0.9:.1f},{speed*0.9:.1f},A,{speed*1.1:.1f},A,{speed*0.95:.1f},A*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class WIMWD(NMEAMessage):
    """Wind direction and speed."""

    def __init__(self, wind_direction: float, wind_speed_knots: float):
        super().__init__("WIMWD")
        self.wind_direction = wind_direction
        self.wind_speed_knots = wind_speed_knots

    def to_string(self) -> str:
        direction = self.add_random_variation(self.wind_direction, 0.1)
        speed = self.add_random_variation(self.wind_speed_knots, 0.1)
        speed_ms = speed * 0.514444

        data = f"$WIMWD,{direction:.1f},T,{direction:.1f},M,{speed:.1f},N,{speed_ms:.1f},M*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class WIMWV(NMEAMessage):
    """Wind speed and angle."""

    def __init__(self, wind_direction: float, wind_speed_knots: float):
        super().__init__("WIMWV")
        self.wind_direction = wind_direction
        self.wind_speed_knots = wind_speed_knots

    def to_string(self) -> str:
        direction = self.add_random_variation(self.wind_direction, 0.1)
        speed = self.add_random_variation(self.wind_speed_knots, 0.1)

        data = f"$WIMWV,{direction:.1f},R,{speed:.1f},N,A*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class IIMTW(NMEAMessage):
    """Water temperature."""

    def __init__(self, temperature_celsius: float):
        super().__init__("IIMTW")
        self.temperature_celsius = temperature_celsius

    def to_string(self) -> str:
        temp = self.add_random_variation(self.temperature_celsius, 0.05)
        data = f"$IIMTW,{temp:.1f},C*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class SDDPT(NMEAMessage):
    """Depth of water."""

    def __init__(self, depth_meters: float, offset: float = 0.3):
        super().__init__("SDDPT")
        self.depth_meters = depth_meters
        self.offset = offset

    def to_string(self) -> str:
        depth = self.add_random_variation(self.depth_meters, 0.1)
        data = f"$SDDPT,{depth:.1f},{self.offset:.1f}*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class SDDBT(NMEAMessage):
    """Depth below transducer."""

    def __init__(self, depth_feet: float, depth_meters: float, depth_fathoms: float):
        super().__init__("SDDBT")
        self.depth_feet = depth_feet
        self.depth_meters = depth_meters
        self.depth_fathoms = depth_fathoms

    def to_string(self) -> str:
        depth_f = self.add_random_variation(self.depth_feet, 0.1)
        depth_m = self.add_random_variation(self.depth_meters, 0.1)
        depth_fathoms = self.add_random_variation(self.depth_fathoms, 0.1)

        data = f"$SDDBT,{depth_f:.1f},f,{depth_m:.1f},M,{depth_fathoms:.1f},F*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class IIRPM(NMEAMessage):
    """Engine RPM."""

    def __init__(self, engine_id: str, rpm: float, pitch: float):
        super().__init__("IIRPM")
        self.engine_id = engine_id
        self.rpm = rpm
        self.pitch = pitch

    def to_string(self) -> str:
        rpm = self.add_random_variation(self.rpm, 0.05)
        pitch = self.add_random_variation(self.pitch, 0.1)

        data = f"$IIRPM,{self.engine_id},{self.engine_id},{rpm:.1f},{pitch:.1f},A*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class IIAPB(NMEAMessage):
    """Autopilot sentence B."""

    def __init__(
        self, bearing_to_dest: float, bearing_to_dest_mag: float, heading: float
    ):
        super().__init__("IIAPB")
        self.bearing_to_dest = bearing_to_dest
        self.bearing_to_dest_mag = bearing_to_dest_mag
        self.heading = heading

    def to_string(self) -> str:
        bearing = self.add_random_variation(self.bearing_to_dest, 0.1)
        bearing_mag = self.add_random_variation(self.bearing_to_dest_mag, 0.1)
        heading = self.add_random_variation(self.heading, 0.1)

        data = f"$IIAPB,A,A,{bearing:.6f},R,N,,,{heading:.1f},T,dest,{bearing_mag:.1f},T,{bearing_mag:.1f},T,A*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class GPRMB(NMEAMessage):
    """Recommended minimum navigation information."""

    def __init__(
        self,
        position: Position,
        bearing: float,
        distance: float,
        speed: float,
        heading: float,
    ):
        super().__init__("GPRMB")
        self.position = position
        self.bearing = bearing
        self.distance = distance
        self.speed = speed
        self.heading = heading

    def to_string(self) -> str:
        lat_str, lat_dir = self.position.to_nmea_lat()
        lon_str, lon_dir = self.position.to_nmea_lon()

        bearing = self.add_random_variation(self.bearing, 0.1)
        distance = self.add_random_variation(self.distance, 0.05)
        speed = self.add_random_variation(self.speed, 0.05)
        heading = self.add_random_variation(self.heading, 0.1)

        data = f"$GPRMB,A,{bearing:.6f},R,origin,dest,{lat_str},{lat_dir},{lon_str},{lon_dir},{distance:.3f},{heading:.1f},-1.4,,A*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class AIVDO(NMEAMessage):
    """AIS VDO (Vessel Data Output) message."""

    def __init__(
        self,
        message_id: int,
        fragment_count: int,
        fragment_number: int,
        radio_channel: str,
        payload: str,
    ):
        super().__init__("AIVDO")
        self.message_id = message_id
        self.fragment_count = fragment_count
        self.fragment_number = fragment_number
        self.radio_channel = radio_channel
        self.payload = payload

    def to_string(self) -> str:
        data = f"!AIVDO,{self.fragment_count},{self.fragment_number},,{self.radio_channel},{self.payload},{self.fragment_number}*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum


class AIVDM(NMEAMessage):
    """AIS VDM (Vessel Data Message) message."""

    def __init__(
        self,
        message_id: int,
        fragment_count: int,
        fragment_number: int,
        radio_channel: str,
        payload: str,
    ):
        super().__init__("AIVDM")
        self.message_id = message_id
        self.fragment_count = fragment_count
        self.fragment_number = fragment_number
        self.radio_channel = radio_channel
        self.payload = payload

    def to_string(self) -> str:
        data = f"!AIVDM,{self.fragment_count},{self.fragment_number},,{self.radio_channel},{self.payload},{self.fragment_number}*"
        checksum = self.calculate_checksum(data[1:-1])
        return data + checksum
