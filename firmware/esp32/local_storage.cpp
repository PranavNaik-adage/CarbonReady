// CarbonReady Local Storage Implementation

#include "local_storage.h"
#include "config.h"
#include <SPIFFS.h>

LocalStorage::LocalStorage() {
  maxReadings = MAX_OFFLINE_READINGS;
}

bool LocalStorage::begin() {
  Serial.println("Initializing SPIFFS...");
  
  if (!SPIFFS.begin(true)) {
    Serial.println("Error: Failed to mount SPIFFS");
    return false;
  }
  
  Serial.println("SPIFFS initialized");
  
  // Print storage info
  size_t totalBytes = SPIFFS.totalBytes();
  size_t usedBytes = SPIFFS.usedBytes();
  Serial.printf("SPIFFS: %d/%d bytes used\n", usedBytes, totalBytes);
  
  return true;
}

bool LocalStorage::storeReading(const String& message) {
  if (isFull()) {
    Serial.println("Warning: Offline storage is full");
    return false;
  }
  
  // Read existing readings
  std::vector<String> readings = readLines();
  
  // Add new reading
  readings.push_back(message);
  
  // Write back to file
  bool success = writeLines(readings);
  
  if (success) {
    Serial.printf("Stored reading offline (%d/%d)\n", 
                  readings.size(), maxReadings);
  } else {
    Serial.println("Error: Failed to store reading");
  }
  
  return success;
}

int LocalStorage::getStoredCount() {
  std::vector<String> readings = readLines();
  return readings.size();
}

std::vector<String> LocalStorage::getAllReadings() {
  return readLines();
}

bool LocalStorage::clearReadings() {
  Serial.println("Clearing offline storage...");
  
  if (SPIFFS.remove(STORAGE_FILE)) {
    Serial.println("Offline storage cleared");
    return true;
  } else {
    Serial.println("Error: Failed to clear offline storage");
    return false;
  }
}

bool LocalStorage::isFull() {
  return getStoredCount() >= maxReadings;
}

std::vector<String> LocalStorage::readLines() {
  std::vector<String> lines;
  
  if (!SPIFFS.exists(STORAGE_FILE)) {
    return lines; // Empty vector
  }
  
  File file = SPIFFS.open(STORAGE_FILE, "r");
  if (!file) {
    Serial.println("Error: Failed to open storage file for reading");
    return lines;
  }
  
  while (file.available()) {
    String line = file.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) {
      lines.push_back(line);
    }
  }
  
  file.close();
  return lines;
}

bool LocalStorage::writeLines(const std::vector<String>& lines) {
  File file = SPIFFS.open(STORAGE_FILE, "w");
  if (!file) {
    Serial.println("Error: Failed to open storage file for writing");
    return false;
  }
  
  for (const String& line : lines) {
    file.println(line);
  }
  
  file.close();
  return true;
}
