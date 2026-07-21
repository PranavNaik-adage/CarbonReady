// CarbonReady Bench Test - RS485 Modbus Soil Sensor
//
// Standalone test sketch for the ZTS-3002-TR-ECTHNPKPH-N01 seven-parameter
// soil sensor (moisture, temperature, EC, pH, N, P, K) over Modbus RTU.
//
// No WiFi, no MQTT, no cloud. Sensor -> Serial Monitor only.
// Raw Modbus RTU implementation, Arduino core only, no external libraries.
//
// Hardware:
//   ESP32-WROOM-32U + MAX485 module + ZTS-3002 sensor on 12V supply
//   GPIO16 = UART2 RX  (MAX485 RO)
//   GPIO17 = UART2 TX  (MAX485 DI)
//   GPIO4  = DE/RE direction control (bridged on MAX485)
//
// Serial Monitor: 115200 baud

#include <Arduino.h>

// Pin configuration
#define RS485_RX_PIN 16   // UART2 RX <- MAX485 RO
#define RS485_TX_PIN 17   // UART2 TX -> MAX485 DI
#define RS485_DE_RE_PIN 4 // HIGH = transmit, LOW = receive

// Modbus configuration (from ZTS-3002 datasheet)
#define SENSOR_SLAVE_ADDR 0x01
#define MODBUS_BAUD 4800
#define REGISTER_COUNT 7
#define RESPONSE_LENGTH 19        // addr(1) + func(1) + count(1) + data(14) + crc(2)
#define RESPONSE_TIMEOUT_MS 1000  // Max wait for a complete response
#define READ_INTERVAL_MS 5000     // Read every 5 seconds

// Time for one character (11 bits: start + 8 data + parity slot + stop) at 4800 baud,
// used as a safety margin when releasing the RS485 bus after transmit
#define CHAR_TIME_US ((11 * 1000000UL) / MODBUS_BAUD)

// Parsed sensor readings
struct SoilReadings {
  float moisture;      // %
  float temperature;   // degrees C (can be negative)
  uint16_t conductivity; // uS/cm
  float ph;            // pH units
  uint16_t nitrogen;   // mg/kg
  uint16_t phosphorus; // mg/kg
  uint16_t potassium;  // mg/kg
};

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n=== CarbonReady RS485 Soil Sensor Bench Test ===");
  Serial.println("Sensor: ZTS-3002-TR-ECTHNPKPH-N01 (7-parameter)");
  Serial.printf("Modbus: slave 0x%02X, %d baud 8N1, FC 0x03, registers 0x0000-0x0006\n\n",
                SENSOR_SLAVE_ADDR, MODBUS_BAUD);

  // Direction control: start in receive mode
  pinMode(RS485_DE_RE_PIN, OUTPUT);
  digitalWrite(RS485_DE_RE_PIN, LOW);

  // UART2 for Modbus
  Serial2.begin(MODBUS_BAUD, SERIAL_8N1, RS485_RX_PIN, RS485_TX_PIN);

  Serial.println("Setup complete. Reading every 5 seconds...\n");
}

void loop() {
  uint8_t response[RESPONSE_LENGTH];
  SoilReadings readings;

  int bytesReceived = sendModbusRequest(response, sizeof(response));

  if (bytesReceived < 0) {
    // Error already printed by sendModbusRequest / validateResponse
  } else if (parseResponse(response, readings)) {
    printReadings(readings);
  }

  delay(READ_INTERVAL_MS);
}

// Compute Modbus CRC16 (polynomial 0xA001, initial value 0xFFFF).
// Returned low byte first on the wire.
uint16_t modbusCRC16(const uint8_t* data, size_t length) {
  uint16_t crc = 0xFFFF;

  for (size_t i = 0; i < length; i++) {
    crc ^= data[i];
    for (int bit = 0; bit < 8; bit++) {
      if (crc & 0x0001) {
        crc = (crc >> 1) ^ 0xA001;
      } else {
        crc >>= 1;
      }
    }
  }

  return crc;
}

// Send the read request and collect the response.
// Returns the number of bytes received, or -1 on error (message already printed).
int sendModbusRequest(uint8_t* response, size_t responseSize) {
  // Request: addr, FC 0x03, start register 0x0000, register count 0x0007, CRC
  uint8_t request[8] = {
    SENSOR_SLAVE_ADDR, 0x03,
    0x00, 0x00,        // start address hi/lo
    0x00, REGISTER_COUNT, // register count hi/lo
    0x00, 0x00         // CRC placeholder
  };

  uint16_t crc = modbusCRC16(request, 6);
  request[6] = crc & 0xFF;        // CRC low byte first
  request[7] = (crc >> 8) & 0xFF;

  // Discard any stale bytes before transmitting
  while (Serial2.available()) {
    Serial2.read();
  }

  // Transmit: assert DE/RE, send, wait for TX to finish, release the bus
  digitalWrite(RS485_DE_RE_PIN, HIGH);
  delayMicroseconds(CHAR_TIME_US); // let the transceiver settle
  Serial2.write(request, sizeof(request));
  Serial2.flush();                 // block until UART FIFO is empty
  delayMicroseconds(CHAR_TIME_US); // margin for the final stop bit
  digitalWrite(RS485_DE_RE_PIN, LOW);

  // Collect response bytes until complete or timeout
  size_t received = 0;
  unsigned long startTime = millis();

  while (received < responseSize && (millis() - startTime) < RESPONSE_TIMEOUT_MS) {
    if (Serial2.available()) {
      response[received++] = Serial2.read();
    }
  }

  // Error case 1: no response at all
  if (received == 0) {
    Serial.println("ERROR: No response (timeout)");
    Serial.println("  Check: sensor 12V power, A/B wiring (try swapping), DE/RE on GPIO4");
    return -1;
  }

  // Error case 2: incomplete response
  if (received < responseSize) {
    Serial.printf("ERROR: Incomplete response (%d/%d bytes)\n", received, responseSize);
    printHexBytes(response, received);
    return -1;
  }

  if (!validateResponse(response, responseSize)) {
    return -1;
  }

  return received;
}

// Validate header and CRC of a complete response.
bool validateResponse(const uint8_t* response, size_t length) {
  // Error case 3: invalid header
  // Expected: addr 0x01, function 0x03, byte count 0x0E (14 data bytes)
  if (response[0] != SENSOR_SLAVE_ADDR ||
      response[1] != 0x03 ||
      response[2] != REGISTER_COUNT * 2) {
    Serial.printf("ERROR: Invalid header (addr=0x%02X func=0x%02X count=0x%02X, "
                  "expected 0x%02X 0x03 0x%02X)\n",
                  response[0], response[1], response[2],
                  SENSOR_SLAVE_ADDR, REGISTER_COUNT * 2);
    // A function code with the high bit set (0x83) is a Modbus exception reply
    if (response[1] == 0x83) {
      Serial.printf("  Sensor returned Modbus exception code 0x%02X\n", response[2]);
    }
    printHexBytes(response, length);
    return false;
  }

  // CRC check (low byte first on the wire)
  uint16_t computedCRC = modbusCRC16(response, length - 2);
  uint16_t receivedCRC = response[length - 2] | (response[length - 1] << 8);

  if (computedCRC != receivedCRC) {
    Serial.printf("ERROR: CRC mismatch (computed 0x%04X, received 0x%04X)\n",
                  computedCRC, receivedCRC);
    printHexBytes(response, length);
    return false;
  }

  return true;
}

// Extract the 7 registers from a validated response and apply datasheet scaling.
bool parseResponse(const uint8_t* response, SoilReadings& readings) {
  // Data starts at byte 3; each register is big-endian (high byte first)
  uint16_t reg[REGISTER_COUNT];
  for (int i = 0; i < REGISTER_COUNT; i++) {
    reg[i] = (response[3 + i * 2] << 8) | response[4 + i * 2];
  }

  readings.moisture     = reg[0] / 10.0f;          // 0x0000: /10 = %
  readings.temperature  = (int16_t)reg[1] / 10.0f; // 0x0001: /10 = C, two's complement
  readings.conductivity = reg[2];                  // 0x0002: uS/cm direct
  readings.ph           = reg[3] / 10.0f;          // 0x0003: /10 = pH
  readings.nitrogen     = reg[4];                  // 0x0004: mg/kg direct
  readings.phosphorus   = reg[5];                  // 0x0005: mg/kg direct
  readings.potassium    = reg[6];                  // 0x0006: mg/kg direct

  return true;
}

void printReadings(const SoilReadings& readings) {
  Serial.println("--- Soil Sensor Readings ---");
  Serial.printf("  Moisture:     %.1f %%\n", readings.moisture);
  Serial.printf("  Temperature:  %.1f C\n", readings.temperature);
  Serial.printf("  Conductivity: %u uS/cm\n", readings.conductivity);
  Serial.printf("  pH:           %.1f\n", readings.ph);
  Serial.printf("  Nitrogen:     %u mg/kg\n", readings.nitrogen);
  Serial.printf("  Phosphorus:   %u mg/kg\n", readings.phosphorus);
  Serial.printf("  Potassium:    %u mg/kg\n", readings.potassium);
  Serial.println();
}

// Dump raw bytes for debugging failed reads.
void printHexBytes(const uint8_t* data, size_t length) {
  Serial.print("  Raw bytes: ");
  for (size_t i = 0; i < length; i++) {
    Serial.printf("%02X ", data[i]);
  }
  Serial.println();
}
