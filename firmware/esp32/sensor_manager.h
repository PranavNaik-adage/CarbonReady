// CarbonReady Sensor Manager
// Handles reading from DHT22, DS18B20, and capacitive soil moisture sensors

#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <Arduino.h>

// Sensor reading structure
struct SensorReadings {
  float soilMoisture;      // Percentage (0-100%)
  float soilTemperature;   // Celsius
  float airTemperature;    // Celsius
  float humidity;          // Percentage (0-100%)
  unsigned long timestamp; // Unix epoch timestamp
  bool valid;              // Indicates if readings are valid
};

class SensorManager {
public:
  SensorManager();
  
  // Initialize all sensors
  bool begin();
  
  // Read all sensors and return readings
  SensorReadings readAllSensors();
  
  // Individual sensor reading functions
  float readSoilMoisture();
  float readSoilTemperature();
  float readAirTemperature();
  float readHumidity();
  
  // Get UTC timestamp
  unsigned long getUTCTimestamp();
  
private:
  bool dht22Initialized;
  bool ds18b20Initialized;
  
  // Validate sensor readings
  bool validateReading(float value, float min, float max);
};

#endif // SENSOR_MANAGER_H
