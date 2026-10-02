import json
from pathlib import Path


MAPPING_FILE = Path(__file__).parent / "treatment_mapping.json"


def load_treatment_mapping():
    """Load disease treatment information from the JSON mapping file."""

    with open(MAPPING_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_treatment(disease_class):
    """
    Return treatment information for a predicted disease.

    Args:
        disease_class (str): Disease class predicted by the classifier.

    Returns:
        dict: Disease, severity, treatment and prevention information.
    """

    mapping = load_treatment_mapping()

    if disease_class not in mapping:
        return {
            "disease": disease_class,
            "severity": "Unknown",
            "treatment": [],
            "prevention": []
        }

    result = mapping[disease_class]

    return {
        "disease": disease_class,
        "severity": result["severity"],
        "treatment": result["treatment"],
        "prevention": result["prevention"]
    }