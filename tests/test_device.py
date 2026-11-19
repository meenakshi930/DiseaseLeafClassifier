from pathlib import Path

from hardware.camera import CameraError
from hardware.device import DeviceRunner, LockedDiagnosis
from hardware.gps import FakeGps, NoGps
from hardware.io import FakeLed, StatusLeds
from hardware.storage.logger import DiagnosisLogger

DISEASE = {"disease": "Tomato_Late_blight", "confidence": 0.93, "is_confident": True,
           "severity": "High", "treatment": [], "prevention": [], "top_k": []}
HEALTHY = dict(DISEASE, disease="Tomato_healthy", severity="None")


class FakeDiagnosis:
    def __init__(self, result):
        self.result = result

    def diagnose(self, image):
        return self.result


class FakeCamera:
    name = "fake"

    def __init__(self, fail=False):
        self.fail = fail

    def capture(self, save_dir):
        if self.fail:
            raise CameraError("not connected")
        path = Path(save_dir) / "photo.jpg"
        path.write_bytes(b"x")
        return path


def build(tmp_path, result=DISEASE, camera=None, gps=None):
    green, red, yellow = FakeLed(), FakeLed(), FakeLed()
    leds = StatusLeds(green, red, yellow, sleep=lambda s: None)
    logger = DiagnosisLogger(tmp_path / "log.csv")
    runner = DeviceRunner(camera or FakeCamera(), FakeDiagnosis(result), logger,
                          leds, tmp_path, gps=gps)
    return runner, logger, (green, red, yellow)


def test_press_diagnoses_logs_and_lights_red(tmp_path):
    runner, logger, (green, red, yellow) = build(tmp_path)
    result = runner.handle_press()
    assert result["disease"] == "Tomato_Late_blight"
    assert red.is_lit and not green.is_lit and not yellow.is_lit
    rows = logger.read_all()
    assert len(rows) == 1 and rows[0]["disease"] == "Tomato_Late_blight"
    assert rows[0]["latitude"] == ""            # no GPS -> empty, not a guess


def test_healthy_lights_green(tmp_path):
    runner, _, (green, red, yellow) = build(tmp_path, result=HEALTHY)
    runner.handle_press()
    assert green.is_lit and not red.is_lit


def test_gps_position_is_logged(tmp_path):
    runner, logger, _ = build(tmp_path, gps=FakeGps(27.5, 77.5))
    runner.handle_press()
    row = logger.read_all()[0]
    assert (row["latitude"], row["longitude"]) == ("27.5", "77.5")


def test_gps_without_fix_logs_empty(tmp_path):
    runner, logger, _ = build(tmp_path, gps=NoGps())
    runner.handle_press()
    assert logger.read_all()[0]["longitude"] == ""


def test_camera_error_blinks_and_logs_nothing(tmp_path):
    runner, logger, (green, red, yellow) = build(tmp_path, camera=FakeCamera(fail=True))
    assert runner.handle_press() is None
    assert logger.read_all() == []
    assert not (green.is_lit or red.is_lit or yellow.is_lit)


def test_crash_in_model_does_not_kill_the_button(tmp_path):
    class Broken:
        def diagnose(self, image):
            raise RuntimeError("model crashed")

    runner, logger, _ = build(tmp_path)
    runner.diagnosis = Broken()
    assert runner.handle_press() is None
    runner.diagnosis = FakeDiagnosis(DISEASE)
    assert runner.handle_press() is not None      # works again afterwards


def test_press_while_busy_is_ignored(tmp_path):
    runner, logger, _ = build(tmp_path)
    runner._busy.acquire()
    assert runner.handle_press() is None
    assert logger.read_all() == []


def test_locked_diagnosis_passes_through():
    assert LockedDiagnosis(FakeDiagnosis(DISEASE)).diagnose("x") == DISEASE
