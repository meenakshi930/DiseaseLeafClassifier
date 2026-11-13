"""The physical device: press the button -> photo -> diagnosis -> log -> LED.

Everything is passed in, so it runs with real hardware on the Pi and with
fakes on the laptop and in tests.
"""

import threading

from hardware.camera import CameraError


class LockedDiagnosis:
    """Only one diagnosis at a time (button and web page share one model)."""

    def __init__(self, diagnosis):
        self._diagnosis = diagnosis
        self._lock = threading.Lock()

    def diagnose(self, image):
        with self._lock:
            return self._diagnosis.diagnose(image)


class DeviceRunner:
    def __init__(self, camera, diagnosis, logger, leds, upload_dir, gps=None):
        self.camera = camera
        self.diagnosis = diagnosis
        self.logger = logger
        self.leds = leds
        self.upload_dir = upload_dir
        self.gps = gps
        self._busy = threading.Lock()
        self.last_result = None

    def handle_press(self):
        """Run one scan. Returns the result dict, or None on error / already busy."""
        if not self._busy.acquire(blocking=False):
            return None                      # second press while working: ignore
        try:
            self.leds.busy()
            try:
                photo = self.camera.capture(self.upload_dir)
            except CameraError as error:
                print(f"Camera error: {error}")
                self.leds.error()
                return None

            result = self.diagnosis.diagnose(str(photo))
            fix = self.gps.get_fix() if self.gps is not None else None
            latitude, longitude = fix if fix else (None, None)
            self.logger.log(result, image_path=photo.name,
                            latitude=latitude, longitude=longitude)

            colour = self.leds.show_result(result)
            self.last_result = result
            print(f"{result['disease']}  {result['confidence'] * 100:.1f}%  "
                  f"-> {colour} LED")
            return result
        except Exception as error:           # never let the button thread die
            print(f"Scan failed: {error}")
            self.leds.error()
            return None
        finally:
            self._busy.release()
