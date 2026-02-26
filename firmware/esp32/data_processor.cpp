// CarbonReady Data Processor Implementation

#include "data_processor.h"
#include <ArduinoJson.h>
#include <mbedtls/sha256.h>
#include <time.h>

DataProcessor::DataProcessor() {
  // Constructor
}

String DataProcessor::createPayload(const SensorReadings& readings,
                                    const String& farmId,
                                    const String& deviceId) {
  // Create JSON document
  StaticJsonDocument<512> doc;
  
  // Add farm and device identifiers
  doc["farmId"] = farmId;
  doc["deviceId"] = deviceId;
  
  // Add timestamp in ISO8601 format
  doc["timestamp"] = formatISO8601(readings.timestamp);
  
  // Add sensor readings
  JsonObject readingsObj = doc.createNestedObject("readings");
  readingsObj["soilMoisture"] = formatFloat(readings.soilMoisture);
  readingsObj["soilTemperature"] = formatFloat(readings.soilTemperature);
  readingsObj["airTemperature"] = formatFloat(readings.airTemperature);
  readingsObj["humidity"] = formatFloat(readings.humidity);
  
  // Serialize to string
  String payload;
  serializeJson(doc, payload);
  
  return payload;
}

String DataProcessor::computeSHA256Hash(const String& payload) {
  // Prepare hash buffer
  uint8_t hash[32];
  
  // Compute SHA-256 hash using mbedtls
  mbedtls_sha256_context ctx;
  mbedtls_sha256_init(&ctx);
  mbedtls_sha256_starts(&ctx, 0); // 0 = SHA-256 (not SHA-224)
  mbedtls_sha256_update(&ctx, (const unsigned char*)payload.c_str(), payload.length());
  mbedtls_sha256_finish(&ctx, hash);
  mbedtls_sha256_free(&ctx);
  
  // Convert hash to hex string
  String hashString = "";
  for (int i = 0; i < 32; i++) {
    char hex[3];
    sprintf(hex, "%02x", hash[i]);
    hashString += hex;
  }
  
  return hashString;
}

bool DataProcessor::compressData(const String& input, uint8_t* output, size_t* outputSize) {
  // Note: For ESP32 with limited resources, we'll skip compression in this implementation
  // to keep memory usage low. The design document mentions compression for cost optimization,
  // but for the pilot phase with small payloads (~200 bytes), the overhead may not be worth it.
  // This can be added later using libraries like miniz or ESP32's built-in compression.
  
  // For now, just copy the data
  memcpy(output, input.c_str(), input.length());
  *outputSize = input.length();
  
  return true;
}

String DataProcessor::createMessage(const SensorReadings& readings,
                                    const String& farmId,
                                    const String& deviceId) {
  // Create payload without hash
  String payload = createPayload(readings, farmId, deviceId);
  
  // Compute hash of payload
  String hash = computeSHA256Hash(payload);
  
  // Parse payload JSON and add hash
  StaticJsonDocument<512> doc;
  deserializeJson(doc, payload);
  doc["hash"] = hash;
  
  // Serialize complete message
  String message;
  serializeJson(doc, message);
  
  Serial.println("Created message with hash:");
  Serial.println(message);
  
  return message;
}

String DataProcessor::formatISO8601(unsigned long timestamp) {
  // Convert Unix timestamp to ISO8601 format
  time_t rawtime = (time_t)timestamp;
  struct tm* timeinfo = gmtime(&rawtime);
  
  char buffer[25];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", timeinfo);
  
  return String(buffer);
}

String DataProcessor::formatFloat(float value) {
  // Format float with 2 decimal places
  char buffer[10];
  snprintf(buffer, sizeof(buffer), "%.2f", value);
  return String(buffer);
}
