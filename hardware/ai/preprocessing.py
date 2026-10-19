import numpy as np
from PIL import Image


IMG_SIZE = (224, 224)


def preprocess_image(image):
    if not isinstance(image, Image.Image):
        image = Image.open(image)

    image = image.convert("RGB")
    image = image.resize(IMG_SIZE, Image.BILINEAR)

    image = np.asarray(image, dtype=np.float32)

    image = np.expand_dims(image, axis=0)

    return image