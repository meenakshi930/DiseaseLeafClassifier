import json

import numpy as np
from PIL import Image


IMG_SIZE = (224, 224)


def load_class_mapping(mapping_path):
    """Load class-index mapping from a JSON file."""

    with open(mapping_path, "r", encoding="utf-8") as file:
        return json.load(file)


def preprocess_for_mobilenet(image_path):
    """
    Prepare an image for the trained MobileNetV3-Small model.

    The trained model uses MobileNetV3's built-in preprocessing,
    so the image remains in the 0-255 float32 range.
    """

    image = Image.open(image_path).convert("RGB")
    image = image.resize(IMG_SIZE)

    image_array = np.asarray(
        image,
        dtype=np.float32
    )

    return np.expand_dims(image_array, axis=0)


def predict_image(image_path, model_path, class_mapping_path):
    """
    Run prediction using the FP32 TFLite model.

    Returns:
        predicted_class: predicted disease/healthy class
        confidence: prediction confidence
    """

    try:
        import tensorflow as tf

        interpreter = tf.lite.Interpreter(
            model_path=str(model_path)
        )

    except ImportError:
        try:
            from tflite_runtime.interpreter import Interpreter

            interpreter = Interpreter(
                model_path=str(model_path)
            )

        except ImportError as error:
            raise ImportError(
                "Install TensorFlow or tflite-runtime "
                "to run TFLite inference."
            ) from error

    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_data = preprocess_for_mobilenet(image_path)

    interpreter.set_tensor(
        input_details[0]["index"],
        input_data
    )

    interpreter.invoke()

    output = interpreter.get_tensor(
        output_details[0]["index"]
    )

    predicted_index = int(np.argmax(output[0]))

    confidence = float(
        output[0][predicted_index]
    )

    class_mapping = load_class_mapping(
        class_mapping_path
    )

    predicted_class = class_mapping[
        str(predicted_index)
    ]

    return predicted_class, confidence