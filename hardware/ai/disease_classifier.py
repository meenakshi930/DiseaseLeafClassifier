from pathlib import Path
import json

import numpy as np

from hardware.ai.preprocessing import preprocess_image


try:
    from ai_edge_litert.interpreter import Interpreter
except ImportError:
    try:
        from tflite_runtime.interpreter import Interpreter
    except ImportError:
        from tensorflow.lite.python.interpreter import Interpreter


MIN_CONFIDENCE = 0.60


class DiseaseClassifier:

    def __init__(
        self,
        model_path=None,
        class_mapping_path=None,
        min_confidence=MIN_CONFIDENCE
    ):

        project_root = Path(__file__).resolve().parents[2]

        if model_path is None:
            model_path = project_root / "model" / "model.tflite"

        if class_mapping_path is None:
            class_mapping_path = project_root / "model" / "class_mapping.json"

        self.model_path = Path(model_path)
        self.class_mapping_path = Path(class_mapping_path)
        self.min_confidence = min_confidence

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}"
            )

        if not self.class_mapping_path.exists():
            raise FileNotFoundError(
                f"Class mapping file not found: {self.class_mapping_path}"
            )

        self.interpreter = Interpreter(
            model_path=str(self.model_path)
        )

        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        with open(
            self.class_mapping_path,
            "r",
            encoding="utf-8"
        ) as file:
            self.class_mapping = json.load(file)

        num_outputs = int(
            self.output_details[0]["shape"][-1]
        )

        if num_outputs != len(self.class_mapping):
            raise ValueError(
                f"Model has {num_outputs} outputs but "
                f"class_mapping.json has {len(self.class_mapping)} classes."
            )
    def get_model_info(self):

        input_info = self.input_details[0]
        output_info = self.output_details[0]

        return {
            "input_shape": input_info["shape"].tolist(),
            "input_dtype": str(input_info["dtype"]),
            "output_shape": output_info["shape"].tolist(),
            "output_dtype": str(output_info["dtype"]),
            "input_quantization": input_info.get("quantization"),
            "output_quantization": output_info.get("quantization")
        }

    def preprocess_image(self, image):
        return preprocess_image(image)

    def predict_image(self, image, top_k=3):

        image_tensor = self.preprocess_image(image)

        return self.predict(
            image_tensor,
            top_k=top_k
        )
    

    @staticmethod
    def quantize_input(values, quantization, dtype):

        scale, zero_point = quantization

        if scale == 0:
            return values.astype(dtype)

        info = np.iinfo(dtype)

        quantized = np.round(
            values / scale + zero_point
        )

        return np.clip(
            quantized,
            info.min,
            info.max
        ).astype(dtype)

    @staticmethod
    def dequantize_output(output, quantization):

        scale, zero_point = quantization

        if scale == 0:
            return output.astype(np.float32)

        return (
            output.astype(np.float32) - zero_point
        ) * scale

    @staticmethod
    def softmax(values):

        values = values.astype(np.float32)

        values = values - np.max(values)

        exp_values = np.exp(values)

        return exp_values / np.sum(exp_values)

    def predict(self, image_tensor, top_k=3):

        image_tensor = np.asarray(image_tensor)

        input_info = self.input_details[0]

        expected_shape = tuple(
            input_info["shape"]
        )

        if image_tensor.shape != expected_shape:
            raise ValueError(
                f"Wrong input shape.\n"
                f"Expected: {expected_shape}\n"
                f"Received: {image_tensor.shape}"
            )

        highest = float(image_tensor.max())

        if 0.0 < highest <= 1.0:
            raise ValueError(
                "Input looks normalized to 0-1. "
                "This model needs pixel values in the range 0-255."
            )

        input_dtype = input_info["dtype"]

        if np.issubdtype(input_dtype, np.integer):

            image_tensor = self.quantize_input(
                image_tensor.astype(np.float32),
                input_info.get(
                    "quantization",
                    (0.0, 0)
                ),
                input_dtype
            )

        else:

            image_tensor = image_tensor.astype(
                input_dtype
            )

        self.interpreter.set_tensor(
            input_info["index"],
            image_tensor
        )

        self.interpreter.invoke()

        output_info = self.output_details[0]

        output = self.interpreter.get_tensor(
            output_info["index"]
        )

        scores = np.squeeze(output)

        if np.issubdtype(output.dtype, np.integer):

            scores = self.dequantize_output(
                scores,
                output_info.get(
                    "quantization",
                    (0.0, 0)
                )
            )

        else:

            scores = scores.astype(np.float32)

        if (
            np.all(scores >= 0)
            and np.all(scores <= 1)
            and np.isclose(
                np.sum(scores),
                1.0,
                atol=0.05
            )
        ):

            probabilities = scores

        else:

            probabilities = self.softmax(scores)

        order = np.argsort(
            probabilities
        )[::-1]

        top = []

        for index in order[:top_k]:

            index = int(index)

            class_name = self.class_mapping.get(
                str(index),
                f"Unknown_Class_{index}"
            )

            top.append({
                "class": class_name,
                "confidence": float(
                    probabilities[index]
                )
            })

        best_index = int(order[0])

        best_confidence = float(
            probabilities[best_index]
        )

        return {
            "class": top[0]["class"],
            "confidence": best_confidence,
            "class_index": best_index,
            "is_confident": (
                best_confidence >= self.min_confidence
            ),
            "top_k": top
        }


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python -m hardware.ai.disease_classifier <image_path>"
        )
        raise SystemExit(1)

    classifier = DiseaseClassifier()

    result = classifier.predict_image(
        sys.argv[1]
    )

    print(
        f"Prediction : {result['class']}"
    )

    print(
        f"Confidence : {result['confidence'] * 100:.1f}%"
    )

    if not result["is_confident"]:
        print(
            "Note       : low confidence, retake the photo"
        )

    print("\nTop predictions:")

    for item in result["top_k"]:

        print(
            f"  {item['confidence'] * 100:5.1f}%  "
            f"{item['class']}"
        )