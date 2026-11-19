"""Guided power test with the USB power meter (the meter has no data cable,
so YOU read the display and type the numbers; this script does the maths).

    python scripts/measure_power.py

Plug the meter between the 5V supply and the Pi. For each state wait ~1 minute,
then read Volts and Amps from the meter. The script asks for them, computes
Watts, saves everything to docs/benchmarks/power_log.csv and estimates
the run time on a power bank.
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "docs" / "benchmarks" / "power_log.csv"

STATES = [
    ("idle", "Pi booted, nothing running"),
    ("web_server", "python main.py running, page open, no scan"),
    ("inference", "press 'Capture and diagnose' repeatedly / run benchmark_latency.py"),
]


def watts(volts, amps):
    return round(volts * amps, 2)


def battery_hours(capacity_mah, power_w, battery_volts=3.7, efficiency=0.85):
    """Rough run time on a power bank: usable energy (Wh) / load (W).

    capacity_mah is the bank's rating at its cell voltage (3.7 V). 85% is a typical
    efficiency of the 5V boost converter. It is an ESTIMATE, not a measurement.
    """
    if power_w <= 0:
        raise ValueError("power must be positive")
    return round(capacity_mah / 1000 * battery_volts * efficiency / power_w, 1)


def ask_float(question):
    while True:
        try:
            value = float(input(question).strip())
            if value > 0:
                return value
        except ValueError:
            pass
        print("  Please type a positive number, e.g. 5.1")


def main():
    rows = []
    for key, description in STATES:
        print(f"\nState: {key}  ({description})")
        input("  Wait about 1 minute, then press Enter... ")
        volts = ask_float("  Volts on the meter: ")
        amps = ask_float("  Amps on the meter : ")
        rows.append({"time": datetime.now().isoformat(timespec="seconds"), "state": key,
                     "volts": volts, "amps": amps, "watts": watts(volts, amps)})
        print(f"  -> {rows[-1]['watts']} W")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    new_file = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["time", "state", "volts", "amps", "watts"])
        if new_file:
            writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved to {LOG}")

    busiest = max(r["watts"] for r in rows)
    capacity = ask_float("\nYour power bank capacity in mAh (printed on it, e.g. 10000): ")
    print(f"Estimated run time at {busiest} W: about "
          f"{battery_hours(capacity, busiest)} hours (estimate, not measured)")


if __name__ == "__main__":
    sys.exit(main())
