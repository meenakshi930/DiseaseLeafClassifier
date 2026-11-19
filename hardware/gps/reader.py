"""GPS readers. All have the same method:  get_fix() -> (latitude, longitude) or None.

    NoGps        - no GPS connected (always None -> log shows empty location)
    GpsReader    - real NEO-6M on /dev/serial0, read in a background thread
    FakeGps      - FIXED coordinates for laptop demos only (never use in real data)
"""

import threading
import time

from hardware.gps.nmea import parse_sentence

DEFAULT_PORT = "/dev/serial0"
DEFAULT_BAUD = 9600                    # NEO-6M default
MAX_FIX_AGE = 30                       # seconds: older fix is not trusted


class NoGps:
    name = "no GPS"

    def get_fix(self):
        return None


class FakeGps:
    """Simulated location. Marked clearly so it is never mistaken for real GPS."""
    name = "FAKE GPS (simulated)"

    def __init__(self, latitude=27.6046, longitude=77.5963):
        self._fix = (latitude, longitude)

    def get_fix(self):
        return self._fix


class GpsReader:
    name = "GPS NEO-6M"

    def __init__(self, port=DEFAULT_PORT, baud=DEFAULT_BAUD, opener=None,
                 clock=time.monotonic, max_age=MAX_FIX_AGE):
        self.port = port
        self.baud = baud
        self._opener = opener                 # tests pass a fake serial port
        self._clock = clock
        self._max_age = max_age
        self._fix = None
        self._fix_time = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None

    def _open(self):
        if self._opener is not None:
            return self._opener()
        import serial                          # pyserial, only needed on the Pi
        return serial.Serial(self.port, self.baud, timeout=1)

    def feed(self, line):
        """Give one NMEA line to the reader. Keeps the fix if the line has one."""
        parsed = parse_sentence(line)
        if parsed is not None:
            with self._lock:
                self._fix = (parsed["latitude"], parsed["longitude"])
                self._fix_time = self._clock()
        return parsed

    def get_fix(self):
        """Latest (lat, lon), or None if there is no fix or it is too old."""
        with self._lock:
            if self._fix is None:
                return None
            if self._clock() - self._fix_time > self._max_age:
                return None
            return self._fix

    def _run(self, port):
        while not self._stop.is_set():
            raw = port.readline()
            if not raw:
                continue
            self.feed(raw.decode("ascii", errors="ignore"))

    def start(self):
        port = self._open()
        self._thread = threading.Thread(target=self._run, args=(port,), daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()


def get_gps(kind="auto"):
    """'auto' = real GPS if the serial port can be opened, else NoGps."""
    kind = (kind or "auto").lower()
    if kind == "none":
        return NoGps()
    if kind == "fake":
        return FakeGps()
    if kind in ("auto", "real"):
        try:
            return GpsReader().start()
        except Exception as error:      # no pyserial or no serial port
            if kind == "real":
                raise RuntimeError(f"GPS not available: {error}")
            return NoGps()
    raise ValueError(f"Unknown gps '{kind}'. Use 'auto', 'real', 'fake' or 'none'.")
