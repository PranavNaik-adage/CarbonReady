// CarbonReady MQTT Client Implementation

#include "mqtt_client.h"
#include "config.h"

MQTTClientManager::MQTTClientManager() : mqttClient(wifiClient) {
  lastRetryCount = 0;
}

bool MQTTClientManager::begin(const String& endpoint,
                               const String& farmId,
                               const String& deviceId,
                               const char* rootCA,
                               const char* deviceCert,
                               const char* deviceKey) {
  this->endpoint = endpoint;
  this->farmId = farmId;
  this->deviceId = deviceId;
  
  // Construct MQTT topics
  this->publishTopic = "carbonready/farm/" + farmId + "/sensor/data";
  this->subscribeTopic = "carbonready/farm/" + farmId + "/commands";
  
  Serial.println("Initializing MQTT client...");
  Serial.printf("Endpoint: %s\n", endpoint.c_str());
  Serial.printf("Publish topic: %s\n", publishTopic.c_str());
  
  // Configure WiFiClientSecure with certificates
  wifiClient.setCACert(rootCA);
  wifiClient.setCertificate(deviceCert);
  wifiClient.setPrivateKey(deviceKey);
  
  // Configure MQTT client
  mqttClient.setServer(endpoint.c_str(), MQTT_PORT);
  mqttClient.setCallback(messageCallback);
  mqttClient.setBufferSize(1024); // Increase buffer for larger messages
  
  Serial.println("MQTT client initialized");
  return true;
}

bool MQTTClientManager::connect() {
  if (mqttClient.connected()) {
    return true;
  }
  
  Serial.println("Connecting to AWS IoT Core...");
  
  // Attempt to connect with device ID as client ID
  if (mqttClient.connect(deviceId.c_str())) {
    Serial.println("Connected to AWS IoT Core");
    
    // Subscribe to command topic
    if (mqttClient.subscribe(subscribeTopic.c_str())) {
      Serial.printf("Subscribed to: %s\n", subscribeTopic.c_str());
    } else {
      Serial.println("Warning: Failed to subscribe to command topic");
    }
    
    return true;
  } else {
    Serial.printf("Connection failed, rc=%d\n", mqttClient.state());
    return false;
  }
}

bool MQTTClientManager::publish(const String& message) {
  // Ensure connected
  if (!isConnected()) {
    Serial.println("Not connected, attempting to connect...");
    if (!connect()) {
      Serial.println("Failed to connect for publish");
      return false;
    }
  }
  
  // Publish with retry logic
  return publishWithRetry(message, MAX_RETRIES);
}

bool MQTTClientManager::publishWithRetry(const String& message, int maxRetries) {
  lastRetryCount = 0;
  
  for (int attempt = 0; attempt <= maxRetries; attempt++) {
    if (attempt > 0) {
      lastRetryCount = attempt;
      unsigned long delay = getBackoffDelay(attempt);
      Serial.printf("Retry attempt %d/%d after %lu ms\n", 
                    attempt, maxRetries, delay);
      ::delay(delay);
      
      // Reconnect if needed
      if (!isConnected()) {
        connect();
      }
    }
    
    // Attempt to publish
    Serial.printf("Publishing to %s (attempt %d/%d)...\n", 
                  publishTopic.c_str(), attempt + 1, maxRetries + 1);
    
    if (mqttClient.publish(publishTopic.c_str(), message.c_str())) {
      Serial.println("Publish successful");
      return true;
    } else {
      Serial.printf("Publish failed, rc=%d\n", mqttClient.state());
    }
  }
  
  Serial.println("All publish attempts failed");
  return false;
}

unsigned long MQTTClientManager::getBackoffDelay(int retryCount) {
  // Exponential backoff: 2^retryCount * base delay
  // Retry 1: 2 seconds
  // Retry 2: 4 seconds
  // Retry 3: 8 seconds
  return RETRY_DELAY_BASE_MS * (1 << retryCount);
}

bool MQTTClientManager::isConnected() {
  return mqttClient.connected();
}

void MQTTClientManager::loop() {
  if (mqttClient.connected()) {
    mqttClient.loop();
  }
}

int MQTTClientManager::getLastRetryCount() {
  return lastRetryCount;
}

void MQTTClientManager::messageCallback(char* topic, byte* payload, unsigned int length) {
  Serial.printf("Message received on topic: %s\n", topic);
  Serial.print("Payload: ");
  for (unsigned int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
  
  // Handle commands here (future enhancement)
  // For now, just log the message
}
