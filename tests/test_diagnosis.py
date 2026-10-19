from PIL import Image

from hardware.ai.diagnosis import Diagnosis


def make_leaf_image(path):
    """Create a small green test image so the test needs no real photo."""
    Image.new("RGB", (256, 256), (50, 120, 50)).save(path)
    return path


def test_diagnosis(tmp_path):
    image_path = make_leaf_image(tmp_path / "leaf.jpg")

    diagnosis = Diagnosis()
    result = diagnosis.diagnose(str(image_path))

    assert "disease" in result
    assert "confidence" in result
    assert "severity" in result
    assert "treatment" in result
    assert "prevention" in result