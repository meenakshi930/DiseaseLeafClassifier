"""Shared pieces for all camera classes."""

import uuid
from pathlib import Path


class CameraError(Exception):
    """Raised when a photo cannot be captured."""


def new_photo_path(save_dir, extension=".jpg"):
    """Return a fresh, random file path inside save_dir (folder is created)."""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir / f"{uuid.uuid4().hex}{extension}"
