"""Read NMEA sentences from the GPS module (NEO-6M) and get latitude/longitude.

A GPS module sends text lines like
    $GPGGA,123519,2736.2800,N,07735.7800,E,1,08,0.9,545.4,M,46.9,M,,*47
Parts we use: UTC time, latitude, N/S, longitude, E/W, fix quality
(0 = no fix), number of satellites. The number after '*' is a checksum.
"""


def checksum_ok(sentence):
    """True if the XOR checksum of '$....*HH' matches HH."""
    sentence = sentence.strip()
    if not sentence.startswith("$") or "*" not in sentence:
        return False
    body, _, given = sentence[1:].partition("*")
    calculated = 0
    for char in body:
        calculated ^= ord(char)
    try:
        return calculated == int(given[:2], 16)
    except ValueError:
        return False


def to_degrees(value, hemisphere):
    """Convert NMEA 'ddmm.mmmm' (or 'dddmm.mmmm') + N/S/E/W to decimal degrees."""
    if not value or hemisphere not in ("N", "S", "E", "W"):
        return None
    try:
        raw = float(value)
    except ValueError:
        return None
    degrees = int(raw // 100)
    minutes = raw - degrees * 100
    result = degrees + minutes / 60
    if hemisphere in ("S", "W"):
        result = -result
    return round(result, 6)


def parse_sentence(sentence):
    """Return a dict {latitude, longitude, satellites} for a GGA sentence with a fix.

    Returns None for: bad checksum, other sentence types, or 'no fix yet'.
    """
    sentence = sentence.strip()
    if not checksum_ok(sentence):
        return None

    fields = sentence[1:].split("*")[0].split(",")
    kind = fields[0][-3:]                       # GPGGA / GNGGA -> 'GGA'
    if kind != "GGA" or len(fields) < 8:
        return None

    fix_quality = fields[6]
    if fix_quality in ("", "0"):
        return None                             # no satellite fix yet

    latitude = to_degrees(fields[2], fields[3])
    longitude = to_degrees(fields[4], fields[5])
    if latitude is None or longitude is None:
        return None

    try:
        satellites = int(fields[7])
    except ValueError:
        satellites = 0
    return {"latitude": latitude, "longitude": longitude, "satellites": satellites}
