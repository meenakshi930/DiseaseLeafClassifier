"""Tests for hardware/ai/disease_classifier.py

Run from the project root:   python -m pytest tests -v
"""

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from hardware.ai.disease_classifier import DiseaseClassifier

MODEL = Path(__file__).resolve().parents[1] / "model" / "model.tflite"

pytestmark = pytest.mark.skipif(not MODEL.exists(), reason="model/model.tflite not found")


@pytest.fixture(scope="module")
def clf():
    return DiseaseClassifier()


def leaf_like_image():
    rng = np.random.default_rng(0)
    arr = (rng.normal(90, 40, (256, 256, 3)) * np.array([0.6, 1.0, 0.5])).clip(0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def test_model_info(clf):
    info = clf.get_model_info()
    assert info["input_shape"] == [1, 224, 224, 3]
    assert info["output_shape"] == [1, 15]


def test_preprocess_shape_and_range(clf):
    batch = clf.preprocess_image(leaf_like_image())
    assert batch.shape == (1, 224, 224, 3)
    assert batch.dtype == np.float32
    assert batch.max() > 1.0            # still 0-255, not 0-1


def test_predict_image_output_format(clf):
    result = clf.predict_image(leaf_like_image())
    assert result["class"] in clf.class_mapping.values()
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["top_k"]) == 3
    confs = [t["confidence"] for t in result["top_k"]]
    assert confs == sorted(confs, reverse=True)
    assert result["top_k"][0]["class"] == result["class"]


def test_predict_matches_predict_image(clf):
    img = leaf_like_image()
    a = clf.predict_image(img)
    b = clf.predict(clf.preprocess_image(img))
    assert a["class"] == b["class"]
    assert a["confidence"] == pytest.approx(b["confidence"])


def test_zero_to_one_input_is_rejected(clf):
    batch = clf.preprocess_image(leaf_like_image()) / 255.0
    with pytest.raises(ValueError):
        clf.predict(batch)


def test_wrong_shape_is_rejected(clf):
    with pytest.raises(ValueError):
        clf.predict(np.zeros((224, 224, 3), np.float32))


def test_black_frame_is_allowed(clf):
    # a covered camera gives an all-black image; it must not crash
    result = clf.predict(np.zeros((1, 224, 224, 3), np.float32))
    assert result["class"] in clf.class_mapping.values()


def test_low_confidence_flag():
    img = leaf_like_image()
    assert DiseaseClassifier(min_confidence=1.01).predict_image(img)["is_confident"] is False
    assert DiseaseClassifier(min_confidence=0.0).predict_image(img)["is_confident"] is True


def test_missing_model_gives_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        DiseaseClassifier(model_path=tmp_path / "nope.tflite")


def test_class_count_mismatch_is_caught(tmp_path):
    bad = tmp_path / "class_mapping.json"
    bad.write_text(json.dumps({"0": "a", "1": "b"}))
    with pytest.raises(ValueError):
        DiseaseClassifier(class_mapping_path=bad)