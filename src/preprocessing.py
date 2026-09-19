from PIL import Image
import numpy as np

IMG_SIZE = (224, 224)


def preprocess_image(image_path):
    """
    Load and preprocess a leaf image.

    Steps:
    1. Convert image to RGB
    2. Resize to 224 x 224
    3. Normalize pixel values to 0-1

    Returns:
        numpy.ndarray: Preprocessed image with shape (224, 224, 3)
    """

    image = Image.open(image_path).convert("RGB")
    image = image.resize(IMG_SIZE)

    image_array = np.array(image, dtype=np.float32)
    image_array = image_array / 255.0

    return image_array
