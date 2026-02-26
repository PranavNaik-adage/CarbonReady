// CarbonReady ESP32 Sensor Configuration
// Hardware: ESP32-WROOM-32
// Sensors: DHT22, DS18B20, Capacitive Soil Moisture

#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration (to be set during provisioning)
#define WIFI_SSID ""
#define WIFI_PASSWORD ""

// AWS IoT Configuration
#define AWS_IOT_ENDPOINT ""  // Set during provisioning
#define MQTT_PORT 8883

// Farm Configuration
#define FARM_ID ""  // Set during provisioning
#define DEVICE_ID ""  // Derived from MAC address

// Sensor Pin Configuration
#define DHT22_PIN 4              // GPIO4 for DHT22 (air temp/humidity)
#define DS18B20_PIN 5            // GPIO5 for DS18B20 (soil temp)
#define SOIL_MOISTURE_PIN 34     // GPIO34 (ADC1_CH6) for capacitive soil moisture

// Timing Configuration
#define READING_INTERVAL_MS (15 * 60 * 1000)  // 15 minutes
#define RETRY_DELAY_BASE_MS 2000               // Initial retry delay
#define MAX_RETRIES 3                          // Maximum transmission retries

// Data Storage
#define MAX_OFFLINE_READINGS 100  // Maximum readings to store offline

// Sensor Calibration Values (set during calibration)
#define SOIL_MOISTURE_DRY 3200    // ADC value for dry soil
#define SOIL_MOISTURE_WET 1200    // ADC value for wet soil

#endif // CONFIG_H
