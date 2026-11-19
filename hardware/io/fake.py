"""Fake button and LED for the laptop and for tests (no GPIO needed)."""


class FakeLed:
    def __init__(self, name=""):
        self.name = name
        self.is_lit = False

    def on(self):
        self.is_lit = True

    def off(self):
        self.is_lit = False


class FakeButton:
    """Call .press() to simulate someone pressing the physical button."""

    def __init__(self):
        self.when_pressed = None

    def press(self):
        if self.when_pressed is not None:
            self.when_pressed()
