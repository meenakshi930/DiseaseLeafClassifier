from hardware.ai.disease_classifier import DiseaseClassifier
from hardware.ai.treatment_mapper import TreatmentMapper


class Diagnosis:

    def __init__(self):
        self.classifier = DiseaseClassifier()
        self.treatment_mapper = TreatmentMapper()

    def diagnose(self, image):

        prediction = self.classifier.predict_image(image)

        treatment = self.treatment_mapper.get_treatment(
            prediction["class"]
        )

        return {
            "disease": prediction["class"],
            "confidence": prediction["confidence"],
            "is_confident": prediction["is_confident"],
            "severity": treatment["severity"],
            "treatment": treatment["treatment"],
            "prevention": treatment["prevention"],
            "top_k": prediction["top_k"]
        }