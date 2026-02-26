// CarbonReady Sensor Manager Implementation

#include "sensor_manager.h"
#include "config.h"
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <time.h>

// DHT22 sensor instance
DHT dht(DHT22_PIN, DHT22);

// DS18B20 sensor instances
OneWire oneWire(DS18B20_PIN);
DallasTemperature ds18b20(&oneWire);

SensorManager::SensorManager() {
  dht22Initialized = false;
  ds18b20Initialized = false;
}

bool SensorManager::begin() {
  Serial.println("Initializing sensors...");
  
  // Initialize DHT22
  dht.begin();
  delay(2000); // DHT22 needs time to stabilize
  dht22Initialized = true;
  Serial.println("DHT22 initialized");
  
  // Initialize DS18B20
  ds18b20.begin();
  int deviceCount = ds18b20.getDeviceCount();
  if (deviceCount > 0) {
    ds18b20Initialized = true;
    Serial.printf("DS18B20 initialized (%d device(s) found)\n", deviceCount);
  } else {
    Serial.println("Warning: No DS18B20 devices found");
    ds18b20Initialized = false;
  }
  
  // Initialize soil moisture sensor (analog pin)
  pinMode(SOIL_MOISTURE_PIN, INPUT);
  Serial.println("Soil moisture sensor initialized");
  
  return dht22Initialized && ds18b20Initialized;
}

SensorReadings SensorManager::readAllSensors() {
  SensorReadings readings;
  readings.valid = false;
  
  Serial.println("Reading sensors...");
  
  // Read all sensors
  readings.soilMoisture = readSoilMoisture();
  readings.soilTemperature = readSoilTemperature();
  readings.airTemperature = readAirTemperature();
  readings.humidity = readHumidity();
  readings.timestamp = getUTCTimestamp();
  
  // Validate all readings
  bool allValid = true;
  allValid &= validateReading(readings.soilMoisture, 0.0, 100.0);
  allValid &= validateReading(readings.soilTemperature, -10.0, 60.0);
  allValid &= validateReading(readings.airTemperature, -10.0, 60.0);
  allValid &= validateReading(readings.humidity, 0.0, 100.0);
  
  readings.valid = allValid;
  
  if (readings.valid) {
    Serial.println("All sensor readings valid");
    Serial.printf("  Soil Moisture: %.2f%%\n", readings.soilMoisture);
    Serial.printf("  Soil Temperature: %.2f°C\n", readings.soilTemperature);
    Serial.printf("  Air Temperature: %.2f°C\n", readings.airTemperature);
    Serial.printf("  Humidity: %.2f%%\n", readings.humidity);
  } else {
    Serial.println("Warning: Some sensor readings are invalid");
  }
  
  return readings;
}

float SensorManager::readSoilMoisture() {
  // Read analog value from capacitive soil moisture sensor
  int rawValue = analogRead(SOIL_MOISTURE_PIN);
  
  // Convert to percentage (0-100%)
  // Lower ADC value = more moisture
  float moisture = 100.0 - ((float)(rawValue - SOIL_MOISTURE_WET) / 
                            (float)(SOIL_MOISTURE_DRY - SOIL_MOISTURE_WET) * 100.0);
  
  // Constrain to valid range
  moisture = constrain(moisture, 0.0, 100.0);
  
  return moisture;
}

float SensorManager::readSoilTemperature() {
  if (!ds18b20Initialized) {
    Serial.println("Error: DS18B20 not initialized");
    return -999.0; // Invalid value
  }
  
  // Request temperature reading
  ds18b20.requestTemperatures();
  
  // Read temperature from first sensor
  float temp = ds18b20.getTempCByIndex(0);
  
  // Check for sensor error
  if (temp == DEVICE_DISCONNECTED_C) {
    Serial.println("Error: DS18B20 disconnected");
    return -999.0;
  }
  
  return temp;
}

float SensorManager::readAirTemperature() {
  if (!dht22Initialized) {
    Serial.println("Error: DHT22 not initialized");
    return -999.0;
  }
  
  float temp = dht.readTemperature();
  
  if (isnan(temp)) {
    Serial.println("Error: Failed to read from DHT22");
    return -999.0;
  }
  
  return temp;
}

float SensorManager::readHumidity() {
  if (!dht22Initialized) {
    Serial.println("Error: DHT22 not initialized");
    return -999.0;
  }
  
  float humidity = dht.readHumidity();
  
  if (isnan(humidity)) {
    Serial.println("Error: Failed to read humidity from DHT22");
    return -999.0;
  }
  
  return humidity;
}

unsigned long SensorManager::getUTCTimestamp() {
  // Get current time from NTP (configured in main setup)
  time_t now;
  time(&now);
  return (unsigned long)now;
}

bool SensorManager::validateReading(float value, float min, float max) {
  // Check for invalid marker value
  if (value <= -999.0) {
    return false;
  }
  
  // Check range
  if (value < min || value > max) {
    Serial.printf("Warning: Reading %.2f out of range [%.2f, %.2f]\n", 
                  value, min, max);
    return false;
  }
  
  return true;
}
