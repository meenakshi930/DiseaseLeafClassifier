import os
import numpy as np
from PIL import Image

from src.preprocessing import preprocess_image


def test_preprocess_image():
    # Create a temporary test image
    test_image_path = "test_image.jpg"

    image = Image.new("RGB", (256, 256), color=(100, 150, 200))
    image.save(test_image_path)

    # Run preprocessing
    result = preprocess_image(test_image_path)

    # Check output shape
    assert result.shape == (224, 224, 3)

    # Check data type
    assert result.dtype == np.float32

    # Check normalization range
    assert result.min() >= 0.0
    assert result.max() <= 1.0

    # Remove temporary image
    os.remove(test_image_path)
