"""Mock camera: pretends to take a photo by handing out sample leaf photos.

Used on the laptop (no Raspberry Pi camera) so the complete flow
capture -> diagnosis -> web page -> log can be tested and demonstrated.
Put some leaf photos in the sample_images/ folder.
"""

import shutil
from pathlib import Path

from hardware.camera.base import CameraError, new_photo_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IMAGE_DIR = PROJECT_ROOT / "sample_images"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class MockCamera:
    name = "mock camera (sample photos)"

    def __init__(self, image_dir=DEFAULT_IMAGE_DIR):
        self.image_dir = Path(image_dir)
        self._next = 0

    def _images(self):
        if not self.image_dir.is_dir():
            return []
        return sorted(p for p in self.image_dir.iterdir()
                      if p.suffix.lower() in IMAGE_EXTENSIONS)

    def capture(self, save_dir):
        """Copy the next sample photo into save_dir and return its path."""
        images = self._images()
        if not images:
            raise CameraError(
                f"Mock camera has no photos. Put leaf photos in {self.image_dir}")

        source = images[self._next % len(images)]       # go round the list
        self._next += 1

        target = new_photo_path(save_dir, source.suffix.lower())
        shutil.copyfile(source, target)
        return target
