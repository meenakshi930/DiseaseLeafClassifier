# Planned pin map (Raspberry Pi 4)

**Status: PLANNED, not tested yet.** Verify each connection on the real Pi
and update this file with what was actually tested.

Numbers are BCM GPIO numbers (physical pin in brackets).

| Part | Connection | Pi pin |
|---|---|---|
| Push button | one leg | GPIO17 (pin 11) |
| Push button | other leg | GND (pin 9) |
| Green LED (healthy / success) | anode via 330 ohm resistor | GPIO27 (pin 13) |
| Red LED (disease found) | anode via 330 ohm resistor | GPIO22 (pin 15) |
| Yellow LED (low confidence / error) | anode via 330 ohm resistor | GPIO23 (pin 16) |
| All LED cathodes (short leg) | | GND (pin 14) |
| GPS NEO-6M VCC | | 3.3 V (pin 1) |
| GPS NEO-6M GND | | GND (pin 6) |
| GPS NEO-6M TX | to Pi RX | GPIO15 / RXD (pin 10) |
| GPS NEO-6M RX | to Pi TX | GPIO14 / TXD (pin 8) |
| Camera module | ribbon cable | CSI camera port |

Notes
- Button: use the Pi's internal pull-up, so the pin reads LOW when pressed.
- Always put a resistor in series with every LED.
- GPS: TX of one device goes to RX of the other (crossed). Enable the serial
  port with `sudo raspi-config` -> Interface Options -> Serial Port:
  login shell = No, serial hardware = Yes. The device is then `/dev/serial0`.
- The GPS gets a fix only with a clear view of the sky (outdoors, can take minutes).
