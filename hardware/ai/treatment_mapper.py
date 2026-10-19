from pathlib import Path
import json


class TreatmentMapper:

    def __init__(self, mapping_path=None):

        project_root = Path(__file__).resolve().parents[2]

        if mapping_path is None:
            mapping_path = project_root / "model" / "treatment_mapping.json"

        self.mapping_path = Path(mapping_path)

        if not self.mapping_path.exists():
            raise FileNotFoundError(
                f"Treatment mapping file not found: {self.mapping_path}"
            )

        with open(
            self.mapping_path,
            "r",
            encoding="utf-8"
        ) as file:
            self.treatment_mapping = json.load(file)

    def get_treatment(self, disease):

        if disease not in self.treatment_mapping:
            raise ValueError(
                f"No treatment found for disease: {disease}"
            )

        data = self.treatment_mapping[disease]

        return {
            "disease": disease,
            "severity": data["severity"],
            "treatment": data["treatment"],
            "prevention": data["prevention"]
        }