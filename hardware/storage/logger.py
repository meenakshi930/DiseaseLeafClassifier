"""CSV logger: saves every diagnosis (time, disease, confidence, GPS) to a file.

Usage:
    from hardware.storage.logger import DiagnosisLogger
    logger = DiagnosisLogger()                       # data_logs/diagnosis_log.csv
    logger.log(result, image_path="leaf.jpg", latitude=27.6, longitude=77.6)
    rows = logger.read_all()
"""

import csv
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_PATH = PROJECT_ROOT / "data_logs" / "diagnosis_log.csv"

FIELDS = [
    "timestamp",
    "image_path",
    "disease",
    "confidence",
    "is_confident",
    "severity",
    "latitude",
    "longitude",
]


class DiagnosisLogger:
    def __init__(self, log_path=DEFAULT_LOG_PATH):
        self.log_path = Path(log_path)
        # create data_logs/ folder if it does not exist
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # write the header row only when the file is new (or empty)
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=FIELDS).writeheader()

    def log(self, result, image_path="", latitude=None, longitude=None):
        """Append one diagnosis result as a new row.

        latitude/longitude can be None (GPS has no fix) -> saved as empty.
        """
        row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "image_path": str(image_path),
            "disease": result["disease"],
            "confidence": round(float(result["confidence"]), 4),
            "is_confident": bool(result["is_confident"]),
            "severity": result["severity"],
            "latitude": "" if latitude is None else latitude,
            "longitude": "" if longitude is None else longitude,
        }
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writerow(row)
        return row

    def read_all(self):
        """Return all saved rows as a list of dicts (oldest first)."""
        with open(self.log_path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))