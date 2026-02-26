# CarbonReady ESP32 Sensor Firmware

This firmware enables ESP32-WROOM-32 microcontrollers to collect environmental data from farms and transmit it securely to AWS IoT Core.

## Hardware Requirements

- **Microcontroller**: ESP32-WROOM-32
- **Sensors**:
  - DHT22: Air temperature and humidity
  - DS18B20: Soil temperature
  - Capacitive soil moisture sensor
- **Total cost target**: ≤₹3,000 per farm

## Pin Configuration

- GPIO4: DHT22 (air temperature/humidity)
- GPIO5: DS18B20 (soil temperature)
- GPIO34: Capacitive soil moisture sensor (analog)

## Features

### Sensor Reading Module (Requirements 1.1-1.6)
- Collects soil moisture, soil temperature, air temperature, and humidity
- Readings every 15 minutes
- UTC timestamp generation
- Data validation (range checking)

### Data Payload Creation (Requirements 16.1-16.2, 13.3)
- JSON payload format
- SHA-256 cryptographic hashing for data integrity
- Compression support (optional)

### MQTT Client (Requirements 3.1, 11.5, 14.2-14.3)
- Secure connection to AWS IoT Core using X.509 certificates
- TLS 1.2+ encryption
- Publishes to: `carbonready/farm/{farmId}/sensor/data`
- Exponential backoff retry (3 attempts: 2s, 4s, 8s)
- Offline data storage when transmission fails

## Building and Flashing

### Using PlatformIO

1. Install PlatformIO: https://platformio.org/install
2. Navigate to firmware directory:
   ```bash
   cd firmware/esp32
   ```
3. Build the firmware:
   ```bash
   pio run
   ```
4. Flash to ESP32:
   ```bash
   pio run --target upload
   ```
5. Monitor serial output:
   ```bash
   pio device monitor
   ```

### Using Arduino IDE

1. Install Arduino IDE: https://www.arduino.cc/en/software
2. Install ESP32 board support:
   - File → Preferences → Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools → Board → Boards Manager → Search "ESP32" → Install
3. Install required libraries:
   - DHT sensor library by Adafruit
   - DallasTemperature by Miles Burton
   - ArduinoJson by Benoit Blanchon
   - PubSubClient by Nick O'Leary
4. Open `carbonready_sensor.ino`
5. Select board: Tools → Board → ESP32 Dev Module
6. Upload to ESP32

## Configuration

Before deploying, configure the following in `config.h`:

```cpp
#define WIFI_SSID "your-wifi-ssid"
#define WIFI_PASSWORD "your-wifi-password"
#define AWS_IOT_ENDPOINT "your-endpoint.iot.region.amazonaws.com"
#define FARM_ID "farm-001"
```

### Certificate Provisioning

X.509 certificates should be stored in SPIFFS (not hardcoded in firmware):

1. Generate device certificates in AWS IoT Core
2. Download: Root CA, device certificate, device private key
3. Upload to SPIFFS using PlatformIO or Arduino IDE
4. Certificates are loaded at runtime from SPIFFS

## Sensor Calibration

### Soil Moisture Sensor

Calibrate the capacitive soil moisture sensor:

1. Measure ADC value in dry soil → Set `SOIL_MOISTURE_DRY`
2. Measure ADC value in wet soil → Set `SOIL_MOISTURE_WET`
3. Update values in `config.h`

Default values:
- Dry: 3200
- Wet: 1200

### Temperature Sensors

DHT22 and DS18B20 are factory calibrated. No additional calibration needed.

## Data Format

### MQTT Payload

```json
{
  "farmId": "farm-001",
  "deviceId": "A1B2C3D4E5F6",
  "timestamp": "2025-01-15T10:30:00Z",
  "readings": {
    "soilMoisture": "45.23",
    "soilTemperature": "22.15",
    "airTemperature": "28.50",
    "humidity": "65.80"
  },
  "hash": "a3f5b8c9d2e1f4a7b6c5d8e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0"
}
```

## Offline Storage

- Stores up to 100 readings when connectivity is lost
- Automatically syncs when connection is restored
- Uses SPIFFS for persistent storage

## Error Handling

- **Sensor failures**: Logs error, skips transmission
- **WiFi disconnection**: Stores data offline
- **MQTT publish failure**: Retries 3 times with exponential backoff
- **Storage full**: Logs warning, discards oldest readings

## Monitoring

Serial output (115200 baud) provides:
- Sensor readings
- Connection status
- Transmission success/failure
- Offline storage status
- Error messages

## Power Consumption

Typical power consumption:
- Active (reading + transmitting): ~160mA @ 3.3V
- Deep sleep (between readings): ~10µA @ 3.3V

For battery operation, implement deep sleep between readings.

## Troubleshooting

### Sensors not reading
- Check pin connections
- Verify sensor power supply (3.3V or 5V depending on sensor)
- Check serial output for initialization errors

### WiFi connection fails
- Verify SSID and password
- Check WiFi signal strength
- Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)

### MQTT connection fails
- Verify AWS IoT endpoint
- Check certificate files in SPIFFS
- Ensure device policy allows publish/subscribe
- Check CloudWatch logs in AWS

### Time sync fails
- Verify internet connectivity
- Check NTP server accessibility
- Ensure firewall allows NTP (UDP port 123)

## Security Considerations

- Certificates stored in SPIFFS (not in firmware)
- TLS 1.2+ encryption for all transmissions
- SHA-256 hash for data integrity verification
- Device-specific X.509 certificates
- No hardcoded credentials in source code

## License

Copyright 2025 CarbonReady Project
