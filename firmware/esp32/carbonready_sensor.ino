// CarbonReady ESP32 Sensor Firmware
// Main application file

#include <WiFi.h>
#include <time.h>
#include "config.h"
#include "sensor_manager.h"
#include "data_processor.h"
#include "mqtt_client.h"
#include "local_storage.h"

// Global instances
SensorManager sensorManager;
DataProcessor dataProcessor;
MQTTClientManager mqttClient;
LocalStorage localStorage;

// Configuration (loaded from SPIFFS during provisioning)
String farmId;
String deviceId;
String awsEndpoint;
String wifiSSID;
String wifiPassword;

// Certificates (loaded from SPIFFS)
String rootCA;
String deviceCert;
String deviceKey;

// Timing
unsigned long lastReadingTime = 0;

void setup() {
  // Initialize serial
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n=== CarbonReady ESP32 Sensor ===");
  
  // Initialize local storage
  if (!localStorage.begin()) {
    Serial.println("Fatal: Failed to initialize storage");
    while (1) delay(1000);
  }
  
  // Load configuration from SPIFFS
  if (!loadConfiguration()) {
    Serial.println("Fatal: Failed to load configuration");
    Serial.println("Please provision the device first");
    while (1) delay(1000);
  }
  
  // Generate device ID from MAC address if not set
  if (deviceId.length() == 0) {
    deviceId = generateDeviceId();
    Serial.printf("Generated device ID: %s\n", deviceId.c_str());
  }
  
  // Connect to WiFi
  connectWiFi();
  
  // Sync time with NTP
  syncTime();
  
  // Initialize sensors
  if (!sensorManager.begin()) {
    Serial.println("Warning: Some sensors failed to initialize");
  }
  
  // Initialize MQTT client
  mqttClient.begin(awsEndpoint, farmId, deviceId,
                   rootCA.c_str(), deviceCert.c_str(), deviceKey.c_str());
  
  // Connect to AWS IoT Core
  if (mqttClient.connect()) {
    Serial.println("Successfully connected to AWS IoT Core");
    
    // Try to sync offline readings
    syncOfflineReadings();
  } else {
    Serial.println("Warning: Failed to connect to AWS IoT Core");
  }
  
  Serial.println("Setup complete");
  Serial.printf("Reading interval: %d minutes\n", READING_INTERVAL_MS / 60000);
}

void loop() {
  // Maintain MQTT connection
  mqttClient.loop();
  
  // Check if it's time for a reading
  unsigned long currentTime = millis();
  if (currentTime - lastReadingTime >= READING_INTERVAL_MS) {
    lastReadingTime = currentTime;
    
    Serial.println("\n--- Taking sensor reading ---");
    
    // Read sensors
    SensorReadings readings = sensorManager.readAllSensors();
    
    if (!readings.valid) {
      Serial.println("Error: Invalid sensor readings, skipping transmission");
      return;
    }
    
    // Create message with hash
    String message = dataProcessor.createMessage(readings, farmId, deviceId);
    
    // Try to publish
    bool published = mqttClient.publish(message);
    
    if (published) {
      Serial.println("Data transmitted successfully");
      
      // If we have offline readings, try to sync them
      if (localStorage.getStoredCount() > 0) {
        syncOfflineReadings();
      }
    } else {
      Serial.println("Failed to transmit data after retries");
      
      // Store offline
      if (localStorage.storeReading(message)) {
        Serial.println("Data stored offline for later transmission");
      } else {
        Serial.println("Error: Failed to store data offline");
      }
    }
  }
  
  // Small delay to prevent watchdog issues
  delay(100);
}

void connectWiFi() {
  Serial.printf("Connecting to WiFi: %s\n", wifiSSID.c_str());
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifiSSID.c_str(), wifiPassword.c_str());
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected");
    Serial.printf("IP address: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\nFailed to connect to WiFi");
  }
}

void syncTime() {
  Serial.println("Syncing time with NTP...");
  
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  
  int attempts = 0;
  time_t now = 0;
  while (now < 1000000000 && attempts < 20) {
    time(&now);
    delay(500);
    attempts++;
  }
  
  if (now > 1000000000) {
    Serial.println("Time synchronized");
    struct tm timeinfo;
    gmtime_r(&now, &timeinfo);
    Serial.printf("Current UTC time: %04d-%02d-%02d %02d:%02d:%02d\n",
                  timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
                  timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
  } else {
    Serial.println("Warning: Failed to sync time");
  }
}

String generateDeviceId() {
  uint8_t mac[6];
  WiFi.macAddress(mac);
  
  char deviceIdBuf[18];
  sprintf(deviceIdBuf, "%02X%02X%02X%02X%02X%02X",
          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  
  return String(deviceIdBuf);
}

bool loadConfiguration() {
  // In a real implementation, this would load from SPIFFS
  // For now, use values from config.h
  
  farmId = String(FARM_ID);
  deviceId = String(DEVICE_ID);
  awsEndpoint = String(AWS_IOT_ENDPOINT);
  wifiSSID = String(WIFI_SSID);
  wifiPassword = String(WIFI_PASSWORD);
  
  // Check if configuration is valid
  if (farmId.length() == 0 || awsEndpoint.length() == 0 || 
      wifiSSID.length() == 0) {
    return false;
  }
  
  // Load certificates from SPIFFS
  // In a real implementation, certificates would be stored in SPIFFS
  // For now, return true if basic config is present
  
  Serial.println("Configuration loaded:");
  Serial.printf("  Farm ID: %s\n", farmId.c_str());
  Serial.printf("  Device ID: %s\n", deviceId.c_str());
  Serial.printf("  AWS Endpoint: %s\n", awsEndpoint.c_str());
  
  return true;
}

void syncOfflineReadings() {
  int storedCount = localStorage.getStoredCount();
  
  if (storedCount == 0) {
    return;
  }
  
  Serial.printf("Syncing %d offline readings...\n", storedCount);
  
  std::vector<String> readings = localStorage.getAllReadings();
  int successCount = 0;
  
  for (const String& reading : readings) {
    if (mqttClient.publish(reading)) {
      successCount++;
    } else {
      Serial.println("Failed to sync offline reading, stopping sync");
      break;
    }
    
    delay(1000); // Delay between messages to avoid overwhelming the broker
  }
  
  if (successCount == storedCount) {
    Serial.printf("Successfully synced all %d offline readings\n", successCount);
    localStorage.clearReadings();
  } else {
    Serial.printf("Synced %d/%d offline readings\n", successCount, storedCount);
    
    // Remove successfully synced readings
    std::vector<String> remainingReadings;
    for (int i = successCount; i < storedCount; i++) {
      remainingReadings.push_back(readings[i]);
    }
    
    localStorage.clearReadings();
    for (const String& reading : remainingReadings) {
      localStorage.storeReading(reading);
    }
  }
}
