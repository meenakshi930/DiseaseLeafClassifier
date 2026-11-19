#!/usr/bin/env bash
# One-command setup on the Raspberry Pi (Raspberry Pi OS, Bookworm).
#
#   cd ~/DiseaseLeafClassifier
#   bash scripts/setup_pi.sh
#
# STATUS: written on a laptop, NOT yet tested on a real Pi. If a step fails,
# read the message, fix it by hand and note it in docs/pi_setup_notes.md.

set -e                                   # stop at the first error
cd "$(dirname "$0")/.."                  # go to the project folder

echo "==> 1/6  Checking this is a Raspberry Pi"
if ! grep -qi "raspberry pi" /proc/device-tree/model 2>/dev/null; then
    echo "This does not look like a Raspberry Pi. Continuing anyway (laptop test)."
fi

echo "==> 2/6  Installing system packages (apt)"
sudo apt update
sudo apt install -y python3-venv python3-pip python3-gpiozero python3-lgpio \
    rpicam-apps git

echo "==> 3/6  Creating virtual environment (keeps apt's gpiozero visible)"
python3 -m venv --system-site-packages venv
# shellcheck disable=SC1091
source venv/bin/activate

echo "==> 4/6  Installing Python packages (this can take a few minutes)"
pip install --upgrade pip
if ! pip install -r requirements-pi.txt; then
    echo "ai-edge-litert not available for this Python. Trying tflite-runtime..."
    grep -v "ai-edge-litert" requirements.txt > /tmp/leaf_req.txt
    echo "pyserial>=3.5" >> /tmp/leaf_req.txt
    pip install -r /tmp/leaf_req.txt
    pip install tflite-runtime
fi

echo "==> 5/6  Enabling the serial port for the GPS (no login console on it)"
if command -v raspi-config >/dev/null 2>&1; then
    sudo raspi-config nonint do_serial_cons 1    # login shell over serial: NO
    sudo raspi-config nonint do_serial_hw 0      # serial hardware port: YES
    echo "Serial enabled. A reboot is needed once:  sudo reboot"
else
    echo "raspi-config not found, skipping serial setup."
fi

echo "==> 6/6  Quick checks"
python - <<'PY'
from hardware.ai.diagnosis import Diagnosis
print("Model loads: OK" if Diagnosis() else "Model: FAILED")
PY
if command -v rpicam-still >/dev/null 2>&1; then
    echo "Camera tool rpicam-still: found"
else
    echo "Camera tool rpicam-still: NOT found (check camera cable, run: rpicam-hello)"
fi

echo
echo "Done. Next:"
echo "  source venv/bin/activate"
echo "  python main.py --once                  # one photo + diagnosis"
echo "  python main.py --device                # button + LEDs + GPS + web page"
