import tensorflow as tf


IMG_SIZE = (224, 224)
NUM_CLASSES = 15


def build_mobilenetv3_model(num_classes=NUM_CLASSES):
    """
    Build the MobileNetV3-Small classifier used for
    the Disease Leaf Classifier project.

    Input:
        RGB images with pixel values in the range 0-255.

    Output:
        Softmax probabilities for the disease classes.
    """

    base_model = tf.keras.applications.MobileNetV3Small(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
        include_preprocessing=True
    )

    base_model.trainable = False

    inputs = tf.keras.Input(
        shape=(*IMG_SIZE, 3),
        name="image"
    )

    x = base_model(inputs, training=False)

    x = tf.keras.layers.GlobalAveragePooling2D()(x)

    x = tf.keras.layers.Dropout(0.2)(x)

    outputs = tf.keras.layers.Dense(
        num_classes,
        activation="softmax",
        name="predictions"
    )(x)

    model = tf.keras.Model(
        inputs=inputs,
        outputs=outputs,
        name="DiseaseLeafClassifier_MobileNetV3Small"
    )

    return model