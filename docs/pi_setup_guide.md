# Raspberry Pi setup guide (do these on the Pi day)

**Status: written before the Pi was available. Nothing here is tested on hardware yet.**
After each step works, tick it and write down anything that was different in `docs/pi_setup_notes.md`.

## 1. Flash the SD card (laptop)
- [ ] Raspberry Pi Imager -> Pi 4 -> **Raspberry Pi OS (64-bit)** -> pick the SD card
- [ ] Settings (gear / Edit settings): hostname `leafpi`, username + password, enable **SSH**,
      Wi-Fi = your phone hotspot (name + password), country India
- [ ] Write, then put the card in the Pi

## 2. First boot
- [ ] Hotspot ON, power the Pi (5V/3A), wait ~2 minutes
- [ ] On laptop: `ssh <username>@leafpi.local` (if it fails, find the Pi's IP in the hotspot's connected-devices list)

## 3. Camera (power OFF before touching the ribbon cable)
- [ ] Lift the black latch of the CSI camera port, push the ribbon cable fully in (check cable direction in the official Pi camera guide, contacts must face the right way), press the latch down, then power ON
- [ ] `rpicam-hello --list-cameras` shows the camera
- [ ] `rpicam-still -o test.jpg` works (copy it to the laptop with `scp` and look at it)

## 4. Get the project and install
- [ ] `git clone -b meenakshi-hardware-dev https://github.com/meenakshi930/DiseaseLeafClassifier.git`
- [ ] `cd DiseaseLeafClassifier && bash scripts/setup_pi.sh`
- [ ] `sudo reboot` once (serial port for GPS), then SSH again

## 5. Run
- [ ] `source venv/bin/activate`
- [ ] `python main.py --once` -> real photo + diagnosis printed
- [ ] `python main.py` -> open `http://leafpi.local:5000` on the phone (same hotspot)

## 6. Button and LEDs (power OFF while wiring, see `docs/pin_map.md`)
- [ ] Wire button (GPIO17 - GND) and 3 LEDs with 330 ohm resistors (GPIO27 green, 22 red, 23 yellow)
- [ ] `python main.py --device --gps none` -> LEDs blink green/red/yellow once at start
- [ ] Press the button -> photo, diagnosis, correct LED

## 7. GPS (go outside / next to a window)
- [ ] Wire NEO-6M per `docs/pin_map.md` (TX->GPIO15, RX->GPIO14, 3.3V, GND)
- [ ] `cat /dev/serial0` shows `$GPGGA...` lines (Ctrl+C to stop)
- [ ] `python main.py --device` -> after a scan, `data_logs/diagnosis_log.csv` has latitude/longitude

## 8. Measurements for the report
- [ ] `python scripts/benchmark_latency.py --runs 30 --camera pi`
- [ ] `python scripts/measure_power.py` (USB power meter between supply and Pi)
- [ ] Update the two yellow placeholder lines in the report with these REAL numbers

## If something breaks
| Problem | Try |
|---|---|
| `leafpi.local` not found | use the Pi's IP from the hotspot device list |
| `rpicam-hello` says no cameras | power off, re-seat the ribbon cable, check cable direction |
| LEDs/button do nothing | check GPIO numbers (BCM, not pin numbers), LED direction (long leg = +) |
| GPS prints nothing | serial enabled? reboot done? TX/RX crossed? Outside with sky view? |
| `ai-edge-litert` install fails | `setup_pi.sh` falls back to `tflite-runtime` automatically |
