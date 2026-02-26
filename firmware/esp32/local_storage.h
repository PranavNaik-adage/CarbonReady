// CarbonReady Local Storage
// Handles offline data storage using SPIFFS

#ifndef LOCAL_STORAGE_H
#define LOCAL_STORAGE_H

#include <Arduino.h>
#include <vector>

class LocalStorage {
public:
  LocalStorage();
  
  // Initialize SPIFFS
  bool begin();
  
  // Store reading offline
  bool storeReading(const String& message);
  
  // Get count of stored readings
  int getStoredCount();
  
  // Get all stored readings
  std::vector<String> getAllReadings();
  
  // Clear stored readings
  bool clearReadings();
  
  // Check if storage is full
  bool isFull();
  
private:
  const char* STORAGE_FILE = "/offline_readings.txt";
  int maxReadings;
  
  // Read all lines from file
  std::vector<String> readLines();
  
  // Write lines to file
  bool writeLines(const std::vector<String>& lines);
};

#endif // LOCAL_STORAGE_H
