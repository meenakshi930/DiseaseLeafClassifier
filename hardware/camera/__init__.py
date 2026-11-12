"""Camera package.

    from hardware.camera import get_camera
    camera = get_camera()            # "auto": Pi camera on the Pi, mock camera elsewhere
    path = camera.capture("data_logs/uploads")

Choose the camera by name (get_camera("mock")) or with the environment
variable LEAF_CAMERA=mock|pi|auto.
"""

import os

from hardware.camera.base import CameraError
from hardware.camera.mock_camera import MockCamera
from hardware.camera.pi_camera import PiCamera

__all__ = ["CameraError", "MockCamera", "PiCamera", "get_camera"]


def get_camera(kind=None):
    """Return a camera object with a .capture(save_dir) method."""
    kind = (kind or os.environ.get("LEAF_CAMERA", "auto")).lower()

    if kind == "mock":
        return MockCamera()
    if kind == "pi":
        return PiCamera()
    if kind == "auto":
        return PiCamera() if PiCamera.is_available() else MockCamera()
    raise ValueError(f"Unknown camera '{kind}'. Use 'auto', 'mock' or 'pi'.")
