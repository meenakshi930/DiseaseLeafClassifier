"""Button + status LEDs on the Raspberry Pi GPIO (BCM numbers, see docs/pin_map.md).

    button, leds = create_io()            # "auto": real GPIO on the Pi, fake elsewhere
    button.when_pressed = my_function
    leds.show_result(result)

Choose with create_io("real") / create_io("fake") or env LEAF_IO=real|fake|auto.
"""

import os
from pathlib import Path

from hardware.io.fake import FakeButton, FakeLed
from hardware.io.leds import StatusLeds, colour_for_result, is_healthy

BUTTON_PIN = 17
GREEN_PIN = 27
RED_PIN = 22
YELLOW_PIN = 23

__all__ = ["BUTTON_PIN", "GREEN_PIN", "RED_PIN", "YELLOW_PIN", "StatusLeds",
           "FakeButton", "FakeLed", "colour_for_result", "is_healthy",
           "on_raspberry_pi", "create_io"]


def on_raspberry_pi():
    """True when this computer is a Raspberry Pi."""
    model = Path("/proc/device-tree/model")
    try:
        return "raspberry pi" in model.read_text(errors="ignore").lower()
    except OSError:
        return False


def _real_io():
    # imported here, so the laptop does not need gpiozero installed
    from gpiozero import LED, Button

    # pull_up=True: pin reads LOW when pressed (button between GPIO17 and GND)
    button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.05)
    leds = StatusLeds(LED(GREEN_PIN), LED(RED_PIN), LED(YELLOW_PIN))
    return button, leds


def _fake_io():
    leds = StatusLeds(FakeLed("green"), FakeLed("red"), FakeLed("yellow"))
    return FakeButton(), leds


def create_io(kind=None):
    """Return (button, leds)."""
    kind = (kind or os.environ.get("LEAF_IO", "auto")).lower()
    if kind == "fake":
        return _fake_io()
    if kind == "real":
        return _real_io()
    if kind == "auto":
        if on_raspberry_pi():
            try:
                return _real_io()
            except ImportError:
                pass                       # gpiozero missing -> fall back to fake
        return _fake_io()
    raise ValueError(f"Unknown io '{kind}'. Use 'auto', 'real' or 'fake'.")
