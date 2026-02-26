// CarbonReady MQTT Client
// Handles secure MQTT connection to AWS IoT Core with retry logic

#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

#include <Arduino.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

class MQTTClientManager {
public:
  MQTTClientManager();
  
  // Initialize MQTT client with certificates
  bool begin(const String& endpoint, 
             const String& farmId,
             const String& deviceId,
             const char* rootCA,
             const char* deviceCert,
             const char* deviceKey);
  
  // Connect to AWS IoT Core
  bool connect();
  
  // Publish message to topic with retry logic
  bool publish(const String& message);
  
  // Check if connected
  bool isConnected();
  
  // Maintain connection (call in loop)
  void loop();
  
  // Get retry count for last publish attempt
  int getLastRetryCount();
  
private:
  WiFiClientSecure wifiClient;
  PubSubClient mqttClient;
  
  String endpoint;
  String farmId;
  String deviceId;
  String publishTopic;
  String subscribeTopic;
  
  int lastRetryCount;
  
  // Retry with exponential backoff
  bool publishWithRetry(const String& message, int maxRetries);
  
  // Calculate exponential backoff delay
  unsigned long getBackoffDelay(int retryCount);
  
  // MQTT callback for subscribed messages
  static void messageCallback(char* topic, byte* payload, unsigned int length);
};

#endif // MQTT_CLIENT_H
