"""Status LEDs: one colour tells the farmer the result at a glance.

    green  = leaf is healthy
    red    = disease found (model is confident)
    yellow = model not sure / error -> retake the photo

The LED objects are passed in (dependency injection), so the same code runs
on the Raspberry Pi (real GPIO LEDs) and on the laptop (FakeLed) and in tests.
"""

import time


def is_healthy(disease_name):
    """True for class names like 'Tomato_healthy' / 'Potato___healthy'."""
    return str(disease_name).lower().endswith("healthy")


def colour_for_result(result):
    """Which LED should light up for a diagnosis dict: 'green', 'red' or 'yellow'."""
    if not result.get("is_confident", False):
        return "yellow"                      # not sure -> never say healthy/diseased
    return "green" if is_healthy(result["disease"]) else "red"


class StatusLeds:
    COLOURS = ("green", "red", "yellow")

    def __init__(self, green, red, yellow, sleep=time.sleep):
        self._leds = {"green": green, "red": red, "yellow": yellow}
        self._sleep = sleep                  # replaced in tests so they run fast

    def all_off(self):
        for led in self._leds.values():
            led.off()

    def show(self, colour):
        """Light exactly one LED (the others go off)."""
        if colour not in self._leds:
            raise ValueError(f"Unknown LED colour '{colour}'")
        self.all_off()
        self._leds[colour].on()

    def show_result(self, result):
        colour = colour_for_result(result)
        self.show(colour)
        return colour

    def busy(self):
        """Yellow on while the photo is being taken and analysed."""
        self.show("yellow")

    def error(self, blinks=3, delay=0.2):
        """Blink yellow: something went wrong (camera error etc.)."""
        self.all_off()
        for _ in range(blinks):
            self._leds["yellow"].on()
            self._sleep(delay)
            self._leds["yellow"].off()
            self._sleep(delay)

    def self_test(self, delay=0.3):
        """Light each LED in turn. Use it to check the wiring."""
        for colour in self.COLOURS:
            self.show(colour)
            self._sleep(delay)
        self.all_off()
