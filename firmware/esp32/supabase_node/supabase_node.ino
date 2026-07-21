// CarbonReady Supabase Node - RS485 Modbus Soil Sensor -> Supabase
//
// Reads the ZTS-3002-TR-ECTHNPKPH-N01 seven-parameter soil sensor over
// Modbus RTU (same code as bench_test.ino) and posts averaged readings to
// a dedicated CarbonReady Supabase project over HTTPS.
//
// Flow:
//   1. Connect WiFi, sync time via NTP
//   2. Auto-register this device (upsert into devices table)
//   3. Every READING_INTERVAL: take BURST_COUNT readings, average valid ones,
//      POST the average to the sensor_readings table
//
// Hardware (unchanged from bench test):
//   ESP32-WROOM-32U + MAX485 module + ZTS-3002 sensor on 12V supply
//   GPIO16 = UART2 RX  (MAX485 RO)
//   GPIO17 = UART2 TX  (MAX485 DI)
//   GPIO4  = DE/RE direction control (bridged on MAX485)
//
// Serial Monitor: 115200 baud

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <time.h>

// ============ USER CONFIGURATION ============
#define WIFI_SSID          "Familywifi-4g"
#define WIFI_PASS          "7720996607"
#define SUPABASE_URL       "https://allovpnwiamzjnmssflk.supabase.co/rest/v1/"
#define SUPABASE_ANON_KEY  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFsbG92cG53aWFtempubXNzZmxrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2NDc3OTQsImV4cCI6MjEwMDIyMzc5NH0.i_FA0nWJPRm-rS6AW6gMojkBbe76O6ZtpSqdbg9RqJ0"
#define DEVICE_ID          "CR-NODE-001"
#define DEVICE_NAME        "CarbonReady Bench Prototype"
#define READING_INTERVAL   60000  // 1 minute in milliseconds
#define BURST_COUNT        3       // readings per burst
#define BURST_DELAY        10000   // 10 seconds between burst readings
// ============================================

// ---- RS485 / Modbus pin configuration (from bench_test.ino) ----
#define RS485_RX_PIN 16   // UART2 RX <- MAX485 RO
#define RS485_TX_PIN 17   // UART2 TX -> MAX485 DI
#define RS485_DE_RE_PIN 4 // HIGH = transmit, LOW = receive

// ---- Modbus configuration (from ZTS-3002 datasheet) ----
#define SENSOR_SLAVE_ADDR 0x01
#define MODBUS_BAUD 4800
#define REGISTER_COUNT 7
#define RESPONSE_LENGTH 19        // addr(1) + func(1) + count(1) + data(14) + crc(2)
#define RESPONSE_TIMEOUT_MS 1000  // Max wait for a complete response

// Time for one character (11 bits) at 4800 baud, used as a safety margin
// when releasing the RS485 bus after transmit
#define CHAR_TIME_US ((11 * 1000000UL) / MODBUS_BAUD)

// ---- WiFi / time ----
#define WIFI_CONNECT_TIMEOUT_MS 20000
#define NTP_SERVER "pool.ntp.org"
#define GMT_OFFSET_SEC 19800  // IST = UTC+5:30
#define DST_OFFSET_SEC 0

// GTS Root R4 - the Google Trust Services root that anchors Supabase's
// *.supabase.co certificate chain (leaf CN=supabase.co <- GTS WE1 <- GTS Root R4).
// Valid 2016-06-22 to 2036-06-22. (Supabase uses Google Trust Services, not
// Let's Encrypt, so the ISRG root does not verify this host.)
static const char GTS_ROOT_R4[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIICCTCCAY6gAwIBAgINAgPlwGjvYxqccpBQUjAKBggqhkjOPQQDAzBHMQswCQYD
VQQGEwJVUzEiMCAGA1UEChMZR29vZ2xlIFRydXN0IFNlcnZpY2VzIExMQzEUMBIG
A1UEAxMLR1RTIFJvb3QgUjQwHhcNMTYwNjIyMDAwMDAwWhcNMzYwNjIyMDAwMDAw
WjBHMQswCQYDVQQGEwJVUzEiMCAGA1UEChMZR29vZ2xlIFRydXN0IFNlcnZpY2Vz
IExMQzEUMBIGA1UEAxMLR1RTIFJvb3QgUjQwdjAQBgcqhkjOPQIBBgUrgQQAIgNi
AATzdHOnaItgrkO4NcWBMHtLSZ37wWHO5t5GvWvVYRg1rkDdc/eJkTBa6zzuhXyi
QHY7qca4R9gq55KRanPpsXI5nymfopjTX15YhmUPoYRlBtHci8nHc8iMai/lxKvR
HYqjQjBAMA4GA1UdDwEB/wQEAwIBhjAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQW
BBSATNbrdP9JNqPV2Py1PsVq8JQdjDAKBggqhkjOPQQDAwNpADBmAjEA6ED/g94D
9J+uHXqnLrmvT/aDHQ4thQEd0dlq7A/Cr8deVl5c1RxYIigL9zC2L7F8AjEA8GE8
p/SgguMh1YQdc4acLa/KNJvxn7kjNuK8YAOdgLOaVsjh4rsUecrNIdSUtUlD
-----END CERTIFICATE-----
)EOF";

// Parsed sensor readings (from bench_test.ino)
struct SoilReadings {
  float moisture;      // %
  float temperature;   // degrees C (can be negative)
  uint16_t conductivity; // uS/cm
  float ph;            // pH units
  uint16_t nitrogen;   // mg/kg
  uint16_t phosphorus; // mg/kg
  uint16_t potassium;  // mg/kg
};

WiFiClientSecure secureClient;
unsigned long lastReadingTime = 0;
bool firstCycleDone = false;

// ---------------------------------------------------------------------------
// Setup / loop
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n=== CarbonReady Supabase Node ===");
  Serial.println("Sensor: ZTS-3002-TR-ECTHNPKPH-N01 (7-parameter)");
  Serial.printf("Device: %s (%s)\n", DEVICE_ID, DEVICE_NAME);
  Serial.printf("Modbus: slave 0x%02X, %d baud 8N1, FC 0x03, registers 0x0000-0x0006\n",
                SENSOR_SLAVE_ADDR, MODBUS_BAUD);

  // Direction control: start in receive mode
  pinMode(RS485_DE_RE_PIN, OUTPUT);
  digitalWrite(RS485_DE_RE_PIN, LOW);

  // UART2 for Modbus
  Serial2.begin(MODBUS_BAUD, SERIAL_8N1, RS485_RX_PIN, RS485_TX_PIN);

  // Trust the GTS Root R4 CA for Supabase HTTPS
  secureClient.setCACert(GTS_ROOT_R4);

  connectWiFi();
  syncTime();
  registerDevice();

  Serial.printf("\nSetup complete. Reading every %lu seconds...\n\n",
                READING_INTERVAL / 1000UL);

  // Take the first reading immediately rather than waiting a full interval
  lastReadingTime = millis() - READING_INTERVAL;
}

void loop() {
  if (millis() - lastReadingTime >= READING_INTERVAL) {
    lastReadingTime = millis();
    runReadingCycle();
    Serial.printf("[%s] Next reading in %lu seconds\n\n",
                  timestampClock().c_str(), READING_INTERVAL / 1000UL);
  }
}

// ---------------------------------------------------------------------------
// Reading cycle: burst of Modbus reads -> average -> POST
// ---------------------------------------------------------------------------

void runReadingCycle() {
  // Accumulators for averaging valid readings
  double sMoisture = 0, sTemp = 0, sEc = 0, sPh = 0, sN = 0, sP = 0, sK = 0;
  int validCount = 0;

  for (int i = 0; i < BURST_COUNT; i++) {
    SoilReadings r;
    if (readSensor(r)) {
      sMoisture += r.moisture;
      sTemp     += r.temperature;
      sEc       += r.conductivity;
      sPh       += r.ph;
      sN        += r.nitrogen;
      sP        += r.phosphorus;
      sK        += r.potassium;
      validCount++;
      Serial.printf("[%s] Burst reading %d/%d... OK (M:%.1f T:%.1f EC:%u pH:%.1f N:%u P:%u K:%u)\n",
                    timestampClock().c_str(), i + 1, BURST_COUNT,
                    r.moisture, r.temperature, r.conductivity, r.ph,
                    r.nitrogen, r.phosphorus, r.potassium);
    } else {
      Serial.printf("[%s] Burst reading %d/%d... FAILED\n",
                    timestampClock().c_str(), i + 1, BURST_COUNT);
    }

    // Wait between burst readings (but not after the last one)
    if (i < BURST_COUNT - 1) {
      delay(BURST_DELAY);
    }
  }

  if (validCount == 0) {
    Serial.printf("[%s] WARNING: all %d burst readings failed, skipping POST\n",
                  timestampClock().c_str(), BURST_COUNT);
    return;
  }

  SoilReadings avg;
  avg.moisture     = sMoisture / validCount;
  avg.temperature  = sTemp / validCount;
  avg.conductivity = (uint16_t)round(sEc / validCount);
  avg.ph           = sPh / validCount;
  avg.nitrogen     = (uint16_t)round(sN / validCount);
  avg.phosphorus   = (uint16_t)round(sP / validCount);
  avg.potassium    = (uint16_t)round(sK / validCount);

  Serial.printf("[%s] Averaged: M:%.1f T:%.1f EC:%u pH:%.1f N:%u P:%u K:%u (%d/%d valid)\n",
                timestampClock().c_str(), avg.moisture, avg.temperature,
                avg.conductivity, avg.ph, avg.nitrogen, avg.phosphorus,
                avg.potassium, validCount, BURST_COUNT);

  postReading(avg);
}

// ---------------------------------------------------------------------------
// Modbus RTU (identical logic to bench_test.ino)
// ---------------------------------------------------------------------------

// Read the sensor once. Returns true and fills `out` on success.
bool readSensor(SoilReadings& out) {
  uint8_t response[RESPONSE_LENGTH];
  if (sendModbusRequest(response, sizeof(response)) < 0) {
    return false;
  }
  return parseResponse(response, out);
}

// Compute Modbus CRC16 (polynomial 0xA001, initial value 0xFFFF).
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
// Returns the number of bytes received, or -1 on error (message printed).
int sendModbusRequest(uint8_t* response, size_t responseSize) {
  uint8_t request[8] = {
    SENSOR_SLAVE_ADDR, 0x03,
    0x00, 0x00,           // start address hi/lo
    0x00, REGISTER_COUNT, // register count hi/lo
    0x00, 0x00            // CRC placeholder
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
    Serial.println("  ERROR: No response (timeout)");
    return -1;
  }

  // Error case 2: incomplete response
  if (received < responseSize) {
    Serial.printf("  ERROR: Incomplete response (%d/%d bytes)\n", received, responseSize);
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
    Serial.printf("  ERROR: Invalid header (addr=0x%02X func=0x%02X count=0x%02X)\n",
                  response[0], response[1], response[2]);
    if (response[1] == 0x83) {
      Serial.printf("    Sensor returned Modbus exception code 0x%02X\n", response[2]);
    }
    printHexBytes(response, length);
    return false;
  }

  // CRC check (low byte first on the wire)
  uint16_t computedCRC = modbusCRC16(response, length - 2);
  uint16_t receivedCRC = response[length - 2] | (response[length - 1] << 8);

  if (computedCRC != receivedCRC) {
    Serial.printf("  ERROR: CRC mismatch (computed 0x%04X, received 0x%04X)\n",
                  computedCRC, receivedCRC);
    printHexBytes(response, length);
    return false;
  }

  return true;
}

// Extract the 7 registers from a validated response and apply datasheet scaling.
bool parseResponse(const uint8_t* response, SoilReadings& readings) {
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

// Dump raw bytes for debugging failed reads.
void printHexBytes(const uint8_t* data, size_t length) {
  Serial.print("    Raw bytes: ");
  for (size_t i = 0; i < length; i++) {
    Serial.printf("%02X ", data[i]);
  }
  Serial.println();
}

// ---------------------------------------------------------------------------
// WiFi
// ---------------------------------------------------------------------------

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.printf("[%s] Connecting to WiFi '%s'...\n", timestampClock().c_str(), WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED &&
         (millis() - start) < WIFI_CONNECT_TIMEOUT_MS) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[%s] WiFi connected, IP %s\n",
                  timestampClock().c_str(), WiFi.localIP().toString().c_str());
  } else {
    Serial.printf("[%s] WiFi connection FAILED (will retry next cycle)\n",
                  timestampClock().c_str());
  }
}

// Ensure WiFi is up before a network operation; reconnect if it dropped.
bool ensureWiFi() {
  if (WiFi.status() == WL_CONNECTED) return true;
  Serial.printf("[%s] WiFi dropped, reconnecting...\n", timestampClock().c_str());
  connectWiFi();
  return WiFi.status() == WL_CONNECTED;
}

// ---------------------------------------------------------------------------
// Time (NTP)
// ---------------------------------------------------------------------------

void syncTime() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.printf("[%s] Skipping NTP sync (no WiFi)\n", timestampClock().c_str());
    return;
  }

  Serial.printf("[--:--:--] Syncing time via NTP (%s)...\n", NTP_SERVER);
  configTime(GMT_OFFSET_SEC, DST_OFFSET_SEC, NTP_SERVER);

  struct tm timeinfo;
  unsigned long start = millis();
  while (!getLocalTime(&timeinfo) && (millis() - start) < 10000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  if (getLocalTime(&timeinfo)) {
    Serial.printf("[%s] Time synced\n", timestampClock().c_str());
  } else {
    Serial.println("[--:--:--] NTP sync FAILED; readings will use server-side now()");
  }
}

bool timeIsSynced() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return false;
  // Before sync the clock sits near the 1970 epoch; treat year >= 2023 as valid
  return (timeinfo.tm_year + 1900) >= 2023;
}

// Short HH:MM:SS clock for serial log lines; falls back to a millis counter.
String timestampClock() {
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    char buf[9];
    strftime(buf, sizeof(buf), "%H:%M:%S", &timeinfo);
    return String(buf);
  }
  unsigned long s = millis() / 1000UL;
  char buf[16];
  snprintf(buf, sizeof(buf), "+%lus", s);
  return String(buf);
}

// ISO 8601 UTC timestamp for Supabase, e.g. "2026-07-21T19:30:00Z".
// Returns empty string if time is not yet synced (caller uses server now()).
String timestampISO8601UTC() {
  if (!timeIsSynced()) return String();

  time_t now = time(nullptr);
  struct tm utc;
  gmtime_r(&now, &utc);
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &utc);
  return String(buf);
}

// ---------------------------------------------------------------------------
// Supabase HTTPS
// ---------------------------------------------------------------------------

// Register (upsert) this device so readings have a valid FK target.
void registerDevice() {
  if (!ensureWiFi()) {
    Serial.printf("[%s] Cannot register device (no WiFi)\n", timestampClock().c_str());
    return;
  }

  String body = String("{\"device_id\":\"") + DEVICE_ID +
                "\",\"name\":\"" + DEVICE_NAME +
                "\",\"is_active\":true,\"firmware_version\":\"1.0.0\"}";

  Serial.printf("[%s] Registering device...\n", timestampClock().c_str());
  int status = supabasePost("/rest/v1/devices", body, true);

  if (status >= 200 && status < 300) {
    Serial.printf("[%s] Device registered (%d)\n", timestampClock().c_str(), status);
  } else {
    Serial.printf("[%s] Device registration returned %d (continuing anyway)\n",
                  timestampClock().c_str(), status);
  }
}

// POST an averaged reading to the sensor_readings table.
void postReading(const SoilReadings& r) {
  if (!ensureWiFi()) {
    Serial.printf("[%s] Cannot POST reading (no WiFi)\n", timestampClock().c_str());
    return;
  }

  String ts = timestampISO8601UTC();

  String body = "{";
  body += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  body += "\"moisture\":" + String(r.moisture, 1) + ",";
  body += "\"temperature\":" + String(r.temperature, 1) + ",";
  body += "\"ec\":" + String((float)r.conductivity, 1) + ",";
  body += "\"ph\":" + String(r.ph, 1) + ",";
  body += "\"nitrogen\":" + String((float)r.nitrogen, 1) + ",";
  body += "\"phosphorus\":" + String((float)r.phosphorus, 1) + ",";
  body += "\"potassium\":" + String((float)r.potassium, 1) + ",";
  if (ts.length() > 0) {
    body += "\"reading_timestamp\":\"" + ts + "\"";
  } else {
    // No NTP time available: let Postgres default (now()) fill it in
    body += "\"reading_timestamp\":\"now()\"";
  }
  body += "}";

  Serial.printf("[%s] POST to Supabase...\n", timestampClock().c_str());
  int status = supabasePost("/rest/v1/sensor_readings", body, false);

  if (status >= 200 && status < 300) {
    Serial.printf("[%s] POST to Supabase... %d %s\n",
                  timestampClock().c_str(), status,
                  status == 201 ? "Created" : "OK");
  } else {
    Serial.printf("[%s] POST FAILED (%d)\n", timestampClock().c_str(), status);
  }
}

// Perform an HTTPS POST to a Supabase REST path.
// Returns the HTTP status code, or a negative value on connection failure.
// `upsert` adds the merge-duplicates Prefer header for device registration.
int supabasePost(const char* path, const String& body, bool upsert) {
  const char* host = supabaseHost();
  if (host == nullptr) {
    Serial.println("  ERROR: could not parse SUPABASE_URL host");
    return -1;
  }

  if (!secureClient.connect(host, 443)) {
    Serial.printf("  ERROR: TLS connect to %s failed\n", host);
    return -2;
  }

  String prefer = upsert ? "resolution=merge-duplicates" : "return=minimal";

  String req = String("POST ") + path + " HTTP/1.1\r\n";
  req += "Host: " + String(host) + "\r\n";
  req += "apikey: " + String(SUPABASE_ANON_KEY) + "\r\n";
  req += "Authorization: Bearer " + String(SUPABASE_ANON_KEY) + "\r\n";
  req += "Content-Type: application/json\r\n";
  req += "Prefer: " + prefer + "\r\n";
  req += "Content-Length: " + String(body.length()) + "\r\n";
  req += "Connection: close\r\n\r\n";
  req += body;

  secureClient.print(req);

  // Read the status line: "HTTP/1.1 201 Created"
  unsigned long start = millis();
  while (!secureClient.available() && (millis() - start) < 10000) {
    delay(10);
  }

  String statusLine = secureClient.readStringUntil('\n');
  int statusCode = -3;
  int firstSpace = statusLine.indexOf(' ');
  if (firstSpace >= 0) {
    statusCode = statusLine.substring(firstSpace + 1, firstSpace + 4).toInt();
  }

  // On error, drain and print the response body to aid debugging
  if (statusCode < 200 || statusCode >= 300) {
    String rest = secureClient.readString();
    int bodyStart = rest.indexOf("\r\n\r\n");
    Serial.printf("  Response: %s\n", statusLine.c_str());
    if (bodyStart >= 0 && bodyStart + 4 < (int)rest.length()) {
      String respBody = rest.substring(bodyStart + 4);
      respBody.trim();
      if (respBody.length() > 0) {
        Serial.printf("  Body: %s\n", respBody.c_str());
      }
    }
  }

  secureClient.stop();
  return statusCode;
}

// Extract the bare host from SUPABASE_URL (strip "https://" and any trailing /).
// Returns a pointer to a static buffer, or nullptr on parse failure.
const char* supabaseHost() {
  static char host[128];
  const char* url = SUPABASE_URL;

  const char* p = strstr(url, "://");
  p = (p != nullptr) ? p + 3 : url;

  size_t i = 0;
  while (*p != '\0' && *p != '/' && *p != ':' && i < sizeof(host) - 1) {
    host[i++] = *p++;
  }
  host[i] = '\0';

  return (i > 0) ? host : nullptr;
}
