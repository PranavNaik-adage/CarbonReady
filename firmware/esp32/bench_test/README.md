# CarbonReady Bench Test — RS485 Modbus Soil Sensor

Standalone test sketch for validating the **ZTS-3002-TR-ECTHNPKPH-N01** seven-parameter
soil sensor before integrating it into the CarbonReady firmware.

No WiFi, no MQTT, no cloud, no external libraries — raw Modbus RTU from the ESP32 to
the sensor, readings printed to the Serial Monitor every 5 seconds.

## Hardware

- ESP32-WROOM-32U dev board
- ZTS-3002-TR-ECTHNPKPH-N01 soil sensor (moisture, temperature, EC, pH, N, P, K)
- MAX485 TTL-to-RS485 module
- 12V DC adapter (sensor power)

## Wiring

| From | To |
|---|---|
| MAX485 RO | ESP32 GPIO16 (UART2 RX) |
| MAX485 DI | ESP32 GPIO17 (UART2 TX) |
| MAX485 DE + RE (bridged) | ESP32 GPIO4 |
| MAX485 VCC | ESP32 3V3 |
| MAX485 GND | Common ground |
| Sensor Yellow | MAX485 terminal A |
| Sensor Blue | MAX485 terminal B |
| Sensor Brown | 12V adapter (+) |
| Sensor Black | 12V adapter (−) |
| 12V adapter GND | Common ground (with ESP32 GND and MAX485 GND) |

**All grounds must be tied together** (12V supply, MAX485, ESP32) or the RS485
transceiver has no common reference and reads will fail intermittently.

## Sensor Modbus Specifications

- Slave address: `0x01` (factory default)
- Serial: 4800 baud, 8 data bits, no parity, 1 stop bit (8N1)
- Function code: `0x03` (read holding registers)
- Query: `01 03 00 00 00 07 [CRC16-lo] [CRC16-hi]`
- Response: 19 bytes = address(1) + function(1) + byte count(1) + data(14) + CRC(2)

### Register map

| Register | Parameter | Conversion |
|---|---|---|
| 0x0000 | Moisture | raw / 10 = % |
| 0x0001 | Temperature | raw / 10 = °C (two's complement for negative) |
| 0x0002 | Conductivity | raw = µS/cm |
| 0x0003 | pH | raw / 10 |
| 0x0004 | Nitrogen | raw = mg/kg |
| 0x0005 | Phosphorus | raw = mg/kg |
| 0x0006 | Potassium | raw = mg/kg |

Registers are big-endian (high byte first). CRC16 uses the standard Modbus
polynomial (0xA001, init 0xFFFF) and is transmitted low byte first.

## Running the Test

### PlatformIO

This folder is its own PIO project (see `platformio.ini` here). From this directory:

```
cd firmware/esp32/bench_test
pio run -t upload
pio device monitor
```

PIO auto-detects the COM port; if it picks the wrong one, list ports with
`pio device list` and pass `--upload-port COM5` (and `-p COM5` for the monitor).

### Arduino IDE

1. Open `bench_test.ino` in the Arduino IDE.
2. Select board **ESP32 Dev Module** (Tools → Board → esp32).
3. Select the correct COM port and upload.
4. Open the Serial Monitor at **115200 baud**.

### Expected output

```
=== CarbonReady RS485 Soil Sensor Bench Test ===
Sensor: ZTS-3002-TR-ECTHNPKPH-N01 (7-parameter)
Modbus: slave 0x01, 4800 baud 8N1, FC 0x03, registers 0x0000-0x0006

Setup complete. Reading every 5 seconds...

--- Soil Sensor Readings ---
  Moisture:     23.4 %
  Temperature:  26.8 C
  Conductivity: 412 uS/cm
  pH:           6.7
  Nitrogen:     48 mg/kg
  Phosphorus:   36 mg/kg
  Potassium:    112 mg/kg
```

With the probe in open air, moisture, EC, and NPK values near zero are normal.
Insert the probe fully into moist soil for meaningful readings.

## Error Handling

The sketch detects and reports three failure modes, printing the raw hex bytes
received in each case to aid debugging:

| Error | Meaning | Likely cause |
|---|---|---|
| `No response (timeout)` | Zero bytes received within 1 s | Sensor unpowered, A/B swapped, DE/RE pin wrong, bad ground |
| `Incomplete response (N/19 bytes)` | Some bytes arrived but fewer than 19 | Baud mismatch, noise, loose wiring, DE/RE released too early |
| `Invalid header` | First 3 bytes ≠ `01 03 0E` | Wrong slave address, Modbus exception reply (function `0x83`), garbage on the bus |

A CRC mismatch on an otherwise complete frame is also detected and reported.

## Troubleshooting

- **Timeout on every read**: swap the A and B wires first — reversed polarity is
  the most common RS485 issue and causes total silence.
- **Garbage / incomplete frames**: confirm 4800 baud (some units ship configured
  for 9600), and keep the RS485 pair away from the 12V supply wiring.
- **Header shows a different address**: the sensor's slave address has been
  changed from the factory default; scan addresses 1–10 by editing
  `SENSOR_SLAVE_ADDR` in the sketch.

## Next Step (not done here)

Once this bench test passes, integrate the Modbus read path into
`firmware/esp32/sensor_manager.cpp`, replacing the DHT22 / DS18B20 / capacitive
moisture readings. Note the pin conflict to resolve at that point: the main
firmware currently uses GPIO4 for the DHT22 (`DHT22_PIN` in `config.h`), while
this bench setup uses GPIO4 for RS485 direction control.
