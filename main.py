"""Start the Leaf Disease Detector.

    python main.py                    # web page on port 5000 (auto camera)
    python main.py --camera mock      # use sample photos instead of the Pi camera
    python main.py --once             # take ONE photo, print the diagnosis, log it

Open the page at http://localhost:5000 (on the Pi: http://leafpi.local:5000).
"""

import argparse
import socket

from hardware.camera import CameraError, get_camera
from hardware.web.app import UPLOAD_DIR, create_app


def local_ip():
    """Best guess of this computer's address on the network (for the phone)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))        # no data is sent
            return s.getsockname()[0]
    except OSError:
        return "localhost"


def run_once(camera):
    from hardware.ai.diagnosis import Diagnosis
    from hardware.storage.logger import DiagnosisLogger

    photo = camera.capture(UPLOAD_DIR)
    result = Diagnosis().diagnose(str(photo))
    DiagnosisLogger().log(result, image_path=photo.name)

    print(f"Photo      : {photo}")
    print(f"Disease    : {result['disease']}")
    print(f"Confidence : {result['confidence'] * 100:.1f}%")
    print(f"Severity   : {result['severity']}")
    if not result["is_confident"]:
        print("Note       : low confidence, retake the photo")


def main():
    parser = argparse.ArgumentParser(description="Leaf Disease Detector")
    parser.add_argument("--camera", default=None, choices=["auto", "mock", "pi"],
                        help="which camera to use (default: auto)")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--once", action="store_true",
                        help="take one photo, print the result and exit")
    args = parser.parse_args()

    camera = get_camera(args.camera)
    print(f"Camera: {camera.name}")

    if args.once:
        try:
            run_once(camera)
        except CameraError as error:
            raise SystemExit(f"Camera error: {error}")
        return

    app = create_app(camera=camera)
    print(f"Open on this computer : http://localhost:{args.port}")
    print(f"Open on your phone    : http://{local_ip()}:{args.port}  (same Wi-Fi)")
    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
