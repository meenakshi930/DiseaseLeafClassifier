from hardware.ai.diagnosis import Diagnosis


def test_diagnosis():

    diagnosis = Diagnosis()

    result = diagnosis.diagnose(
        "sample_images/leaf.jpg"
    )

    assert "disease" in result
    assert "confidence" in result
    assert "severity" in result
    assert "treatment" in result
    assert "prevention" in result