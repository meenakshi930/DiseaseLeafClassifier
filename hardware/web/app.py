"""Flask web page: upload / capture a leaf photo and see the diagnosis.

Run from the project root:
    python -m hardware.web.app
then open  http://localhost:5000  (on the Pi: http://leafpi.local:5000
from any phone/laptop on the same Wi-Fi / hotspot).
"""

import uuid
from pathlib import Path

from flask import Flask, abort, render_template, request, send_from_directory
from PIL import Image, UnidentifiedImageError

from hardware.storage.logger import DiagnosisLogger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "data_logs" / "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# model class name -> readable name for the page
DISPLAY_NAMES = {
    "Pepper__bell___Bacterial_spot": "Pepper (bell) - Bacterial spot",
    "Pepper__bell___healthy": "Pepper (bell) - Healthy",
    "Potato___Early_blight": "Potato - Early blight",
    "Potato___Late_blight": "Potato - Late blight",
    "Potato___healthy": "Potato - Healthy",
    "Tomato_Bacterial_spot": "Tomato - Bacterial spot",
    "Tomato_Early_blight": "Tomato - Early blight",
    "Tomato_Late_blight": "Tomato - Late blight",
    "Tomato_Leaf_Mold": "Tomato - Leaf mold",
    "Tomato_Septoria_leaf_spot": "Tomato - Septoria leaf spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "Tomato - Spider mites",
    "Tomato__Target_Spot": "Tomato - Target spot",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "Tomato - Yellow leaf curl virus",
    "Tomato__Tomato_mosaic_virus": "Tomato - Mosaic virus",
    "Tomato_healthy": "Tomato - Healthy",
}


def pretty_name(class_name):
    """Readable disease name; falls back to the raw name if unknown."""
    return DISPLAY_NAMES.get(class_name, class_name.replace("_", " ").strip())


def create_app(diagnosis=None, logger=None, upload_dir=UPLOAD_DIR):
    """App factory. Tests pass a fake `diagnosis` / `logger` / `upload_dir`."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024      # 10 MB uploads

    upload_dir = Path(upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # The model is loaded ONCE here (the slow part), not on every request.
    if diagnosis is None:
        from hardware.ai.diagnosis import Diagnosis
        diagnosis = Diagnosis()
    if logger is None:
        logger = DiagnosisLogger()

    app.jinja_env.filters["pretty"] = pretty_name

    @app.route("/")
    def index():
        return render_template("index.html", error=None)

    @app.route("/diagnose", methods=["POST"])
    def diagnose():
        file = request.files.get("image")
        if file is None or file.filename == "":
            return render_template("index.html", error="Please choose a photo first."), 400

        extension = Path(file.filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            return render_template(
                "index.html", error="Unsupported file type. Use JPG or PNG."), 400

        # random file name -> user-given names are never trusted
        saved = upload_dir / f"{uuid.uuid4().hex}{extension}"
        file.save(saved)

        try:
            Image.open(saved).verify()                       # is it a real image?
        except (UnidentifiedImageError, OSError):
            saved.unlink(missing_ok=True)
            return render_template(
                "index.html", error="That file is not a valid image."), 400

        result = diagnosis.diagnose(str(saved))
        logger.log(result, image_path=saved.name)            # GPS added later
        return render_template("result.html", r=result, image_name=saved.name)

    @app.route("/uploads/<name>")
    def uploads(name):
        return send_from_directory(upload_dir, name)

    @app.route("/history")
    def history():
        rows = list(reversed(logger.read_all()))[:20]        # newest first
        return render_template("history.html", rows=rows)

    return app


if __name__ == "__main__":
    # host 0.0.0.0 = reachable from other devices (phone) on the same network
    create_app().run(host="0.0.0.0", port=5000, debug=False)