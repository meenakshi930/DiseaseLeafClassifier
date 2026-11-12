"""Raspberry Pi camera.

Uses the command line tool that comes with Raspberry Pi OS
(rpicam-still on new versions, libcamera-still on older ones), so no extra
Python package is needed.
"""

import shutil
import subprocess

from hardware.camera.base import CameraError, new_photo_path

COMMANDS = ("rpicam-still", "libcamera-still")


class PiCamera:
    name = "Raspberry Pi camera"

    def __init__(self, width=1280, height=960, warmup_ms=1500, command=None):
        self.width = width
        self.height = height
        self.warmup_ms = warmup_ms          # time for auto exposure to settle
        self.command = command

    @staticmethod
    def find_command():
        for name in COMMANDS:
            if shutil.which(name):
                return name
        return None

    @classmethod
    def is_available(cls):
        return cls.find_command() is not None

    def capture(self, save_dir):
        """Take one photo, save it in save_dir and return its path."""
        command = self.command or self.find_command()
        if command is None:
            raise CameraError(
                "Camera tool not found (rpicam-still / libcamera-still). "
                "Is this a Raspberry Pi with the camera enabled?")

        path = new_photo_path(save_dir, ".jpg")
        arguments = [command, "-n",                       # -n: no preview window
                     "-t", str(self.warmup_ms),
                     "--width", str(self.width),
                     "--height", str(self.height),
                     "-o", str(path)]

        try:
            subprocess.run(arguments, check=True, capture_output=True, timeout=20)
        except subprocess.TimeoutExpired as error:
            raise CameraError("The camera did not respond in time.") from error
        except subprocess.CalledProcessError as error:
            detail = error.stderr.decode(errors="replace").strip()[-200:]
            raise CameraError(f"Camera command failed: {detail}") from error

        if not path.exists() or path.stat().st_size == 0:
            raise CameraError("The camera produced no image file.")
        return path
