# Demo guide (laptop)

How to run and present the Leaf Disease Detector without the Raspberry Pi.
The same commands work on the Pi later (use `source venv/bin/activate` there).

## 1. One-time setup
```
.\venv\Scripts\Activate.ps1            # PowerShell  (Git Bash: source venv/Scripts/activate)
pip install ai-edge-litert pillow numpy pytest flask
```
Put 4-6 good leaf photos in `sample_images/` (one leaf, plain background,
leaf filling the frame; some healthy, some diseased). The mock camera hands
them out one by one.

## 2. Show that everything is tested
```
python -m pytest tests -v              # expect: 35 passed
```

## 3. Start the system
```
python main.py --camera mock
```
It prints two addresses:
- `http://localhost:5000` - open on the laptop
- `http://<laptop-ip>:5000` - open on a phone connected to the same Wi-Fi

## 4. Demo steps (about 2 minutes)
1. Open the page. Say: "On the Raspberry Pi this button takes a photo with the
   Pi camera. On the laptop a mock camera gives sample photos."
2. Press **Capture and diagnose**. Show the result card: disease, severity
   badge, confidence bar, treatment, prevention, other possibilities.
3. Press **Scan another leaf** and capture again with a different photo
   (ideally one healthy, one diseased).
4. Show a phone: upload a leaf photo with **Choose File** (the phone camera opens).
5. Open **History** and show the saved scans.
6. Optional: show `data_logs/diagnosis_log.csv` in Excel.
7. Show GitHub: separate commits, folders (`ai`, `camera`, `storage`, `web`).

## 5. If something goes wrong
| Problem | Fix |
|---|---|
| "Mock camera has no photos" | Put photos in `sample_images/` |
| Phone cannot open the page | Phone and laptop must be on the same Wi-Fi; allow Python in the Windows firewall popup |
| "No module named ..." | The venv is not active: run the Activate command again |
| A photo gives a wrong or low-confidence result | Use another photo. The model works best on PlantVillage-style photos (one leaf, plain background) |

## 6. What to say about limits (be honest)
- Accuracy is 93.21% on lab-style test images; real field photos can be lower.
- The model has no "not a leaf" class, so other plants can get a wrong answer.
- Camera, GPS, button/LED on the Raspberry Pi are still to be tested.
