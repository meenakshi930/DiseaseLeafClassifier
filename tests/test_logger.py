from hardware.storage.logger import FIELDS, DiagnosisLogger

RESULT = {
    "disease": "Tomato_Early_blight",
    "confidence": 0.91234,
    "is_confident": True,
    "severity": "Medium",
    "treatment": "x",
    "prevention": "y",
    "top_k": [],
}


def test_creates_folder_file_and_header(tmp_path):
    path = tmp_path / "new_folder" / "log.csv"
    DiagnosisLogger(log_path=path)
    assert path.exists()
    assert path.read_text().splitlines()[0] == ",".join(FIELDS)


def test_log_and_read_back(tmp_path):
    logger = DiagnosisLogger(log_path=tmp_path / "log.csv")
    logger.log(RESULT, image_path="leaf.jpg", latitude=27.6, longitude=77.6)
    rows = logger.read_all()
    assert len(rows) == 1
    assert rows[0]["disease"] == "Tomato_Early_blight"
    assert rows[0]["confidence"] == "0.9123"
    assert rows[0]["latitude"] == "27.6"


def test_missing_gps_is_saved_empty(tmp_path):
    logger = DiagnosisLogger(log_path=tmp_path / "log.csv")
    logger.log(RESULT)
    row = logger.read_all()[0]
    assert row["latitude"] == "" and row["longitude"] == ""


def test_rows_are_appended_and_header_not_repeated(tmp_path):
    path = tmp_path / "log.csv"
    DiagnosisLogger(log_path=path).log(RESULT)
    DiagnosisLogger(log_path=path).log(RESULT)   # re-open the same file
    assert len(DiagnosisLogger(log_path=path).read_all()) == 2
    assert path.read_text().count("timestamp") == 1