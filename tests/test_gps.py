import pytest

from hardware.gps import FakeGps, GpsReader, NoGps, checksum_ok, get_gps, parse_sentence, to_degrees


def with_checksum(body):
    value = 0
    for char in body:
        value ^= ord(char)
    return f"${body}*{value:02X}"


GOOD = with_checksum("GPGGA,123519,2736.2800,N,07735.7800,E,1,08,0.9,545.4,M,46.9,M,,")
NO_FIX = with_checksum("GPGGA,123519,,,,,0,00,99.9,,M,,M,,")


def test_known_checksum_example():
    # the classic textbook sentence
    assert checksum_ok("$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47")


def test_bad_checksum_rejected():
    assert not checksum_ok(GOOD[:-2] + "00")
    assert not checksum_ok("garbage")
    assert not checksum_ok("$GPGGA,no,star")


def test_to_degrees():
    assert to_degrees("2736.2800", "N") == pytest.approx(27.604667, abs=1e-6)
    assert to_degrees("07735.7800", "E") == pytest.approx(77.596333, abs=1e-6)
    assert to_degrees("2736.2800", "S") < 0
    assert to_degrees("07735.7800", "W") < 0
    assert to_degrees("", "N") is None
    assert to_degrees("abc", "N") is None
    assert to_degrees("2736.28", "X") is None


def test_parse_good_gga():
    fix = parse_sentence(GOOD)
    assert fix["latitude"] == pytest.approx(27.604667, abs=1e-6)
    assert fix["longitude"] == pytest.approx(77.596333, abs=1e-6)
    assert fix["satellites"] == 8


def test_parse_no_fix_and_other_sentences():
    assert parse_sentence(NO_FIX) is None
    assert parse_sentence(with_checksum("GPVTG,0.0,T,,M,0.0,N,0.0,K,N")) is None
    assert parse_sentence(GOOD[:-2] + "00") is None          # corrupted line


def test_gn_talker_also_works():
    line = with_checksum("GNGGA,123519,2736.2800,N,07735.7800,E,1,08,0.9,545.4,M,46.9,M,,")
    assert parse_sentence(line) is not None


def test_reader_keeps_fix_and_ignores_junk():
    reader = GpsReader()
    assert reader.get_fix() is None
    reader.feed("hello")
    reader.feed(NO_FIX)
    assert reader.get_fix() is None
    reader.feed(GOOD)
    lat, lon = reader.get_fix()
    assert lat == pytest.approx(27.604667, abs=1e-6)


def test_old_fix_is_dropped():
    now = [0.0]
    reader = GpsReader(clock=lambda: now[0], max_age=30)
    reader.feed(GOOD)
    now[0] = 10
    assert reader.get_fix() is not None
    now[0] = 31
    assert reader.get_fix() is None


def test_reader_thread_reads_from_fake_serial():
    import time

    class FakePort:
        def __init__(self):
            self.lines = [b"junk\r\n", GOOD.encode() + b"\r\n"]

        def readline(self):
            time.sleep(0.01)
            return self.lines.pop(0) if self.lines else b""

    reader = GpsReader(opener=FakePort).start()
    for _ in range(100):
        if reader.get_fix():
            break
        time.sleep(0.02)
    reader.stop()
    assert reader.get_fix() is not None


def test_other_gps_kinds():
    assert NoGps().get_fix() is None
    assert FakeGps().get_fix() == (27.6046, 77.5963)
    assert "FAKE" in FakeGps().name
    assert isinstance(get_gps("none"), NoGps)
    with pytest.raises(ValueError):
        get_gps("banana")
