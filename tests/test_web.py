import io
from pathlib import Path

import pytest
from PIL import Image

from hardware.camera import CameraError
from hardware.storage.logger import DiagnosisLogger
from hardware.web.app import create_app, pretty_name

FAKE_RESULT = {
    "disease": "Tomato_Late_blight",
    "confidence": 0.93,
    "is_confident": True,
    "severity": "High",
    "treatment": ["Remove infected leaves."],
    "prevention": ["Avoid overhead watering."],
    "top_k": [{"class": "Tomato_Late_blight", "confidence": 0.93},
              {"class": "Tomato_Early_blight", "confidence": 0.04}],
}


class FakeDiagnosis:
    def __init__(self, result=FAKE_RESULT):
        self.result = result

    def diagnose(self, image):
        return self.result


class FakeCamera:
    name = "fake camera"

    def __init__(self, fail=False):
        self.fail = fail

    def capture(self, save_dir):
        if self.fail:
            raise CameraError("Camera not connected")
        path = Path(save_dir) / "captured.png"
        Image.new("RGB", (64, 64), (40, 120, 40)).save(path)
        return path


@pytest.fixture
def client(tmp_path):
    app = create_app(
        diagnosis=FakeDiagnosis(),
        logger=DiagnosisLogger(log_path=tmp_path / "log.csv"),
        upload_dir=tmp_path / "uploads",
        camera=FakeCamera(),
    )
    return app.test_client()


def png_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), (40, 120, 40)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Scan a leaf" in response.data


def test_diagnose_shows_result(client):
    response = client.post("/diagnose", data={"image": (png_bytes(), "leaf.png")},
                           content_type="multipart/form-data")
    assert response.status_code == 200
    assert b"Tomato - Late blight" in response.data
    assert b"93.0%" in response.data
    assert b"Remove infected leaves." in response.data
    assert b"Low confidence" not in response.data


def test_low_confidence_warning(tmp_path):
    low = dict(FAKE_RESULT, confidence=0.4, is_confident=False)
    app = create_app(diagnosis=FakeDiagnosis(low),
                     logger=DiagnosisLogger(log_path=tmp_path / "log.csv"),
                     upload_dir=tmp_path / "uploads", camera=FakeCamera())
    response = app.test_client().post(
        "/diagnose", data={"image": (png_bytes(), "leaf.png")},
        content_type="multipart/form-data")
    assert b"Low confidence" in response.data
    # advice for an uncertain prediction must not be shown
    assert b"Remove infected leaves." not in response.data
    assert b"hidden because the model is not sure" in response.data


def test_no_file_is_rejected(client):
    response = client.post("/diagnose", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert b"choose a photo" in response.data


def test_wrong_extension_is_rejected(client):
    response = client.post("/diagnose", data={"image": (io.BytesIO(b"hi"), "notes.txt")},
                           content_type="multipart/form-data")
    assert response.status_code == 400


def test_fake_image_content_is_rejected(client):
    response = client.post("/diagnose", data={"image": (io.BytesIO(b"not an image"), "x.jpg")},
                           content_type="multipart/form-data")
    assert response.status_code == 400
    assert b"not a valid image" in response.data


def test_scan_is_logged_and_shown_in_history(client):
    client.post("/diagnose", data={"image": (png_bytes(), "leaf.png")},
                content_type="multipart/form-data")
    response = client.get("/history")
    assert response.status_code == 200
    assert b"Tomato - Late blight" in response.data


def test_pretty_name_known_and_unknown():
    assert pretty_name("Tomato_healthy") == "Tomato - Healthy"
    assert pretty_name("Some_new_class") == "Some new class"

def test_capture_button_takes_photo_and_shows_result(client):
    response = client.post("/capture")
    assert response.status_code == 200
    assert b"Tomato - Late blight" in response.data
    assert b"Remove infected leaves." in response.data


def test_capture_is_logged(client):
    client.post("/capture")
    assert b"Tomato - Late blight" in client.get("/history").data


def test_capture_camera_error_is_shown(tmp_path):
    app = create_app(diagnosis=FakeDiagnosis(),
                     logger=DiagnosisLogger(log_path=tmp_path / "log.csv"),
                     upload_dir=tmp_path / "uploads", camera=FakeCamera(fail=True))
    response = app.test_client().post("/capture")
    assert response.status_code == 503
    assert b"Camera not connected" in response.data


def test_home_page_has_capture_button_and_camera_name(client):
    page = client.get("/").data
    assert b"Capture and diagnose" in page
    assert b"fake camera" in page
