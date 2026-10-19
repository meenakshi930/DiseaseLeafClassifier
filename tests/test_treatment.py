from hardware.ai.treatment_mapper import TreatmentMapper


def test_treatment_mapping():

    mapper = TreatmentMapper()

    result = mapper.get_treatment("Potato___Late_blight")

    assert result["disease"] == "Potato___Late_blight"
    assert result["severity"] == "High"
    assert len(result["treatment"]) > 0
    assert len(result["prevention"]) > 0