// CarbonReady Data Processor
// Handles JSON payload creation, SHA-256 hashing, and data compression

#ifndef DATA_PROCESSOR_H
#define DATA_PROCESSOR_H

#include <Arduino.h>
#include "sensor_manager.h"

class DataProcessor {
public:
  DataProcessor();
  
  // Create JSON payload from sensor readings
  String createPayload(const SensorReadings& readings, 
                       const String& farmId, 
                       const String& deviceId);
  
  // Compute SHA-256 hash of payload
  String computeSHA256Hash(const String& payload);
  
  // Compress data before transmission (gzip)
  bool compressData(const String& input, uint8_t* output, size_t* outputSize);
  
  // Create complete message with hash
  String createMessage(const SensorReadings& readings,
                       const String& farmId,
                       const String& deviceId);
  
private:
  // Format timestamp as ISO8601
  String formatISO8601(unsigned long timestamp);
  
  // Format float with 2 decimal places
  String formatFloat(float value);
};

#endif // DATA_PROCESSOR_H
