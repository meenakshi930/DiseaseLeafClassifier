from src.treatment.treatment_mapper import get_treatment
from src.treatment.treatment_mapper import load_treatment_mapping


def test_all_disease_classes_are_mapped():
    mapping = load_treatment_mapping()

    assert len(mapping) == 15

    for disease_class in mapping:
        result = get_treatment(disease_class)

        assert result["disease"] == disease_class
        assert result["severity"] in ["Low", "Medium", "High"]
        assert len(result["treatment"]) > 0
        assert len(result["prevention"]) > 0


def test_known_disease():
    result = get_treatment(
        "Pepper__bell___Bacterial_spot"
    )

    assert result["severity"] == "Medium"
    assert len(result["treatment"]) > 0
    assert len(result["prevention"]) > 0


def test_unknown_disease():
    result = get_treatment("Unknown_Disease")

    assert result["disease"] == "Unknown_Disease"
    assert result["severity"] == "Unknown"
    assert result["treatment"] == []
    assert result["prevention"] == []