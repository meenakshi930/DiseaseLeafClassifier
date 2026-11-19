"""Measure how long one diagnosis takes (the 'latency' test of the project).

    python scripts/benchmark_latency.py                  # 30 runs on sample_images/
    python scripts/benchmark_latency.py --runs 50 --camera pi

Measures, separately:
  * inference  = preprocess + model + treatment lookup  (Diagnosis.diagnose)
  * capture    = camera.capture()  (only with --camera)
  * total      = capture + inference
The first run is a warm-up and is NOT counted. Results go to
docs/benchmarks/latency_<machine>.json so Pi and laptop numbers stay separate.
Run it on the Pi for the real edge numbers; a laptop number must be labelled as a laptop number.
"""

import argparse
import json
import platform
import statistics
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def summarize(times_ms):
    """mean / median / p95 / min / max of a list of times in milliseconds."""
    ordered = sorted(times_ms)
    p95_index = max(0, min(len(ordered) - 1, round(0.95 * len(ordered)) - 1))
    return {
        "runs": len(ordered),
        "mean_ms": round(statistics.mean(ordered), 1),
        "median_ms": round(statistics.median(ordered), 1),
        "p95_ms": round(ordered[p95_index], 1),
        "min_ms": round(ordered[0], 1),
        "max_ms": round(ordered[-1], 1),
    }


def cpu_temperature():
    """CPU temperature in Celsius (Linux/Pi), or None."""
    try:
        text = Path("/sys/class/thermal/thermal_zone0/temp").read_text()
        return round(int(text) / 1000, 1)
    except (OSError, ValueError):
        return None


def machine_name():
    try:
        model = Path("/proc/device-tree/model").read_text(errors="ignore")
        return model.strip("\x00 \n")
    except OSError:
        return f"{platform.system()} {platform.machine()}"


def list_images(folder):
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)


def run_benchmark(diagnose, images, runs, camera=None, save_dir=None, clock=time.perf_counter):
    """Return (inference_times_ms, capture_times_ms). `diagnose` takes a path string."""
    inference, capture = [], []
    for i in range(runs + 1):                       # +1 = warm-up run
        capture_ms = 0.0
        if camera is not None:
            start = clock()
            image = camera.capture(save_dir)
            capture_ms = (clock() - start) * 1000
        else:
            image = images[i % len(images)]

        start = clock()
        diagnose(str(image))
        inference_ms = (clock() - start) * 1000

        if i == 0:
            continue                                # warm-up: not counted
        inference.append(inference_ms)
        if camera is not None:
            capture.append(capture_ms)
    return inference, capture


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--images", default=str(ROOT / "sample_images"))
    parser.add_argument("--camera", default=None, choices=["mock", "pi"],
                        help="also time the camera capture")
    args = parser.parse_args()

    from hardware.ai.diagnosis import Diagnosis

    images = list_images(args.images) if Path(args.images).is_dir() else []
    camera = None
    if args.camera:
        from hardware.camera import get_camera
        camera = get_camera(args.camera)
    elif not images:
        raise SystemExit(f"No photos in {args.images}. Add leaf photos or use --camera.")

    print(f"Machine: {machine_name()}   |   CPU temp before: {cpu_temperature()} C")
    t0 = time.perf_counter()
    diagnosis = Diagnosis()
    load_ms = (time.perf_counter() - t0) * 1000
    print(f"Model load time (one time, at start-up): {load_ms:.0f} ms")

    with tempfile.TemporaryDirectory() as tmp:
        inference, capture = run_benchmark(diagnosis.diagnose, images, args.runs,
                                           camera=camera, save_dir=tmp)

    report = {
        "machine": machine_name(),
        "python": platform.python_version(),
        "date": datetime.now().isoformat(timespec="seconds"),
        "model_load_ms": round(load_ms),
        "inference": summarize(inference),
        "cpu_temp_after_c": cpu_temperature(),
    }
    if capture:
        report["capture"] = summarize(capture)
        report["total"] = summarize([a + b for a, b in zip(capture, inference)])

    print("\n| Step | mean | median | p95 | min | max |  (ms)")
    print("|---|---|---|---|---|---|")
    for name in ("capture", "inference", "total"):
        if name in report:
            s = report[name]
            print(f"| {name} | {s['mean_ms']} | {s['median_ms']} | {s['p95_ms']} | "
                  f"{s['min_ms']} | {s['max_ms']} |")
    print(f"\nCPU temp after: {report['cpu_temp_after_c']} C")

    out_dir = ROOT / "docs" / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in machine_name())[:40]
    out = out_dir / f"latency_{safe}.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
