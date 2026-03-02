# CarbonReady Test Firmware (No Sensors Required)

This firmware allows you to test the complete CarbonReady system using only an ESP32 - no physical sensors needed!

## What It Does

- Generates realistic simulated sensor readings
- Connects to WiFi and AWS IoT Core
- Publishes data every 15 minutes
- Tests the complete end-to-end data flow

## Setup Instructions

1. **Copy the template:**
   ```bash
   cp test_without_sensors.ino.template test_without_sensors.ino
   ```

2. **Update WiFi credentials** in `test_without_sensors.ino`:
   ```cpp
   const char* WIFI_SSID = "YourActualWiFiName";
   const char* WIFI_PASSWORD = "YourActualPassword";
   ```

3. **Update AWS IoT endpoint**:
   ```cpp
   const char* AWS_IOT_ENDPOINT = "your-endpoint.iot.region.amazonaws.com";
   ```

4. **Provision your device** to get certificates:
   ```bash
   python scripts/provision_device.py esp32-test farm-001
   ```

5. **Paste certificates** from `device_certs/esp32-test/`:
   - Copy `AmazonRootCA1.pem` → paste into `AWS_CERT_CA`
   - Copy `device.crt` → paste into `AWS_CERT_CRT`
   - Copy `device.key` → paste into `AWS_CERT_PRIVATE`

6. **Upload to ESP32** using Arduino IDE

7. **Monitor Serial output** (115200 baud) to verify connection

## Security Note

⚠️ **NEVER commit `test_without_sensors.ino` with your actual credentials!**

The `.gitignore` file is configured to exclude this file. Always use the `.template` file for version control.

## Simulated Data Ranges

- Soil Moisture: 30-70%
- Soil Temperature: 20-28°C
- Air Temperature: 25-35°C
- Humidity: 50-80%

## Troubleshooting

See `TESTING_WITHOUT_SENSORS.md` in the project root for detailed troubleshooting steps.
