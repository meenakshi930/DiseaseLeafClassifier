"""GPS (NEO-6M) location for every scan.

    from hardware.gps import get_gps
    gps = get_gps()                 # real GPS on the Pi, NoGps elsewhere
    fix = gps.get_fix()             # (latitude, longitude) or None
"""

from hardware.gps.nmea import checksum_ok, parse_sentence, to_degrees
from hardware.gps.reader import FakeGps, GpsReader, NoGps, get_gps

__all__ = ["checksum_ok", "parse_sentence", "to_degrees",
           "FakeGps", "GpsReader", "NoGps", "get_gps"]
