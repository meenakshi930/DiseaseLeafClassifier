import pytest

from hardware.io import FakeButton, FakeLed, StatusLeds, create_io, colour_for_result, is_healthy


def make_leds():
    green, red, yellow = FakeLed("green"), FakeLed("red"), FakeLed("yellow")
    leds = StatusLeds(green, red, yellow, sleep=lambda s: None)   # no real waiting
    return leds, green, red, yellow


def result(disease, confident=True):
    return {"disease": disease, "confidence": 0.9, "is_confident": confident}


def test_is_healthy():
    assert is_healthy("Tomato_healthy")
    assert is_healthy("Potato___healthy")
    assert is_healthy("Pepper__bell___healthy")
    assert not is_healthy("Tomato_Late_blight")


def test_colour_green_for_healthy():
    assert colour_for_result(result("Tomato_healthy")) == "green"


def test_colour_red_for_disease():
    assert colour_for_result(result("Tomato_Late_blight")) == "red"


def test_colour_yellow_when_not_confident_even_if_healthy():
    assert colour_for_result(result("Tomato_healthy", confident=False)) == "yellow"
    assert colour_for_result(result("Tomato_Late_blight", confident=False)) == "yellow"


def test_show_result_lights_only_one_led():
    leds, green, red, yellow = make_leds()
    yellow.on()
    assert leds.show_result(result("Tomato_Late_blight")) == "red"
    assert (green.is_lit, red.is_lit, yellow.is_lit) == (False, True, False)


def test_all_off_and_unknown_colour():
    leds, green, red, yellow = make_leds()
    leds.show("green")
    leds.all_off()
    assert not green.is_lit
    with pytest.raises(ValueError):
        leds.show("blue")


def test_error_blinks_and_ends_off():
    events = []

    class Recorder(FakeLed):
        def on(self):
            events.append("on")
            super().on()

    leds = StatusLeds(FakeLed(), FakeLed(), Recorder(), sleep=lambda s: None)
    leds.error(blinks=3)
    assert events == ["on", "on", "on"]


def test_self_test_ends_with_everything_off():
    leds, green, red, yellow = make_leds()
    leds.self_test()
    assert not (green.is_lit or red.is_lit or yellow.is_lit)


def test_fake_button_calls_callback():
    button = FakeButton()
    pressed = []
    button.when_pressed = lambda: pressed.append(1)
    button.press()
    assert pressed == [1]
    FakeButton().press()                  # no callback set: must not crash


def test_create_io_fake_and_unknown():
    button, leds = create_io("fake")
    assert isinstance(button, FakeButton)
    with pytest.raises(ValueError):
        create_io("banana")
