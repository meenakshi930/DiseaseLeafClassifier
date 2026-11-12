import subprocess

import pytest
from PIL import Image

from hardware.camera import CameraError, MockCamera, PiCamera, get_camera


def make_photos(folder, names):
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        Image.new("RGB", (32, 32), (40, 120, 40)).save(folder / name)


def test_mock_camera_copies_a_sample_photo(tmp_path):
    make_photos(tmp_path / "samples", ["a.jpg"])
    path = MockCamera(tmp_path / "samples").capture(tmp_path / "out")
    assert path.exists() and path.parent == tmp_path / "out"


def test_mock_camera_goes_round_the_photos(tmp_path):
    make_photos(tmp_path / "samples", ["a.png", "b.png"])
    camera = MockCamera(tmp_path / "samples")
    sizes = []
    for _ in range(3):                      # a, b, a again
        sizes.append(camera.capture(tmp_path / "out").stat().st_size)
    assert sizes[0] == sizes[2]
    assert len(list((tmp_path / "out").iterdir())) == 3


def test_mock_camera_without_photos_gives_clear_error(tmp_path):
    with pytest.raises(CameraError, match="no photos"):
        MockCamera(tmp_path / "empty").capture(tmp_path / "out")


def test_pi_camera_runs_the_command_and_returns_the_file(tmp_path, monkeypatch):
    seen = {}

    def fake_run(arguments, **kwargs):
        seen["arguments"] = arguments
        open(arguments[arguments.index("-o") + 1], "wb").write(b"jpeg-bytes")
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    path = PiCamera(command="rpicam-still").capture(tmp_path)
    assert path.exists() and path.suffix == ".jpg"
    assert seen["arguments"][0] == "rpicam-still"
    assert "--width" in seen["arguments"]


def test_pi_camera_command_failure_is_reported(tmp_path, monkeypatch):
    def fake_run(arguments, **kwargs):
        raise subprocess.CalledProcessError(1, arguments, stderr=b"no camera detected")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(CameraError, match="no camera detected"):
        PiCamera(command="rpicam-still").capture(tmp_path)


def test_pi_camera_without_tool_gives_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(PiCamera, "find_command", staticmethod(lambda: None))
    with pytest.raises(CameraError, match="not found"):
        PiCamera().capture(tmp_path)


def test_get_camera_choices(monkeypatch):
    assert isinstance(get_camera("mock"), MockCamera)
    assert isinstance(get_camera("pi"), PiCamera)
    monkeypatch.setattr(PiCamera, "is_available", classmethod(lambda cls: False))
    assert isinstance(get_camera("auto"), MockCamera)
    monkeypatch.setattr(PiCamera, "is_available", classmethod(lambda cls: True))
    assert isinstance(get_camera("auto"), PiCamera)
    monkeypatch.setenv("LEAF_CAMERA", "mock")
    assert isinstance(get_camera(), MockCamera)
    with pytest.raises(ValueError):
        get_camera("webcam")
