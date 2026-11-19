import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bench = load("benchmark_latency")
power = load("measure_power")


def test_summarize():
    s = bench.summarize([10, 20, 30, 40, 100])
    assert s["runs"] == 5 and s["mean_ms"] == 40 and s["median_ms"] == 30
    assert s["min_ms"] == 10 and s["max_ms"] == 100 and s["p95_ms"] == 100


def test_run_benchmark_skips_warmup_and_counts_runs():
    calls = []
    ticks = iter(range(0, 10_000, 5))              # fake clock: every call +5 s

    inference, capture = bench.run_benchmark(
        lambda path: calls.append(path), ["a.jpg", "b.jpg"], runs=4,
        clock=lambda: next(ticks) / 1000)
    assert len(calls) == 5                         # 4 runs + 1 warm-up
    assert len(inference) == 4 and capture == []
    assert all(abs(t - 5) < 0.001 for t in inference)   # 5 ms each


def test_run_benchmark_with_camera():
    class Cam:
        def capture(self, save_dir):
            return Path(save_dir) / "x.jpg"

    inference, capture = bench.run_benchmark(lambda p: None, [], runs=3, camera=Cam(),
                                             save_dir="/tmp")
    assert len(inference) == 3 and len(capture) == 3


def test_power_maths():
    assert power.watts(5.1, 0.8) == 4.08
    # 10000 mAh at 3.7 V = 37 Wh; 85% usable = 31.45 Wh; at 5 W -> 6.3 h
    assert power.battery_hours(10000, 5.0) == 6.3


def test_power_rejects_zero():
    import pytest
    with pytest.raises(ValueError):
        power.battery_hours(10000, 0)
