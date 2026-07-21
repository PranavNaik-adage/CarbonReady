# CarbonReady Supabase Node

ESP32 firmware that reads the **ZTS-3002-TR-ECTHNPKPH-N01** seven-parameter soil
sensor over RS485 Modbus and posts averaged readings to a dedicated **CarbonReady
Supabase** project over WiFi/HTTPS.

The Modbus read path is the exact code proven in
[`../bench_test/bench_test.ino`](../bench_test/bench_test.ino) — same pins, CRC16,
parsing, two's-complement temperature handling, and error cases. This sketch adds
WiFi, NTP time sync, device auto-registration, and the Supabase POST.

## Data flow

```
ZTS-3002 sensor
   │  RS485 (Modbus RTU, 4800 8N1)
   ▼
MAX485  ──►  ESP32 (GPIO16/17 UART2, GPIO4 DE/RE)
   │  read 7 registers, average a burst of readings
   ▼
WiFi ──► HTTPS POST ──► CarbonReady Supabase
                          ├─ /rest/v1/devices        (upsert, once at boot)
                          └─ /rest/v1/sensor_readings (every READING_INTERVAL)
```

## Hardware (unchanged from bench test)

| From | To |
|---|---|
| MAX485 RO | ESP32 GPIO16 (UART2 RX) |
| MAX485 DI | ESP32 GPIO17 (UART2 TX) |
| MAX485 DE + RE (bridged) | ESP32 GPIO4 |
| MAX485 VCC | ESP32 3V3 |
| MAX485 GND | Common ground |
| Sensor Yellow | MAX485 terminal A |
| Sensor Blue | MAX485 terminal B |
| Sensor Brown | 12V adapter (+) |
| Sensor Black | 12V adapter (−) |
| 12V adapter GND | Common ground (ESP32 + MAX485) |

ESP32 powered over USB (or regulated 3.3V). **All grounds must be tied together.**

## Configuration

Open `supabase_node.ino` and fill in the block at the top:

```cpp
// ============ USER CONFIGURATION ============
#define WIFI_SSID          "your-wifi-ssid"
#define WIFI_PASS          "your-wifi-password"
#define SUPABASE_URL       "https://xxxxx.supabase.co"   // from Supabase > Settings > API
#define SUPABASE_ANON_KEY  "eyJ...your-anon-key"          // the anon/public key
#define DEVICE_ID          "CR-NODE-001"                  // unique per physical node
#define DEVICE_NAME        "CarbonReady Bench Prototype"
#define READING_INTERVAL   300000  // 5 minutes in milliseconds
#define BURST_COUNT        3       // readings per burst
#define BURST_DELAY        10000   // 10 seconds between burst readings
// ============================================
```

Notes:
- **2.4 GHz WiFi only** — the ESP32 does not support 5 GHz networks.
- `SUPABASE_URL` must be the full `https://` project URL, no trailing slash.
- Use the **anon/public** key, not the service-role/secret key. The RLS policies
  in `firmware/supabase/001_initial_schema.sql` allow anonymous inserts.
- `DEVICE_ID` must be unique for each node you deploy. The device row is upserted,
  so re-flashing the same `DEVICE_ID` is safe (no duplicates).

The **GTS Root R4** CA certificate (Google Trust Services, which issues Supabase's
`*.supabase.co` chain: leaf ← GTS WE1 ← GTS Root R4) is already embedded — no need
to change it. It is valid until 2036-06-22. (Supabase does **not** use Let's
Encrypt, so an ISRG root will not verify the host.)

## Flashing

### PlatformIO

```
cd firmware/esp32/supabase_node
pio run -t upload
pio device monitor
```

`pio` auto-detects the COM port; if it picks the wrong one, run `pio device list`
and pass `--upload-port COM5` (and `-p COM5` for the monitor).

### Arduino IDE

1. Open `supabase_node.ino`.
2. Board: **ESP32 Dev Module** (Tools → Board → esp32).
3. Select the COM port and upload.
4. Open the Serial Monitor at **115200 baud**.

Only ESP32 Arduino core libraries are used (`WiFi`, `WiFiClientSecure`) — there
are no external library dependencies to install.

## Expected serial output

```
=== CarbonReady Supabase Node ===
Sensor: ZTS-3002-TR-ECTHNPKPH-N01 (7-parameter)
Device: CR-NODE-001 (CarbonReady Bench Prototype)
Modbus: slave 0x01, 4800 baud 8N1, FC 0x03, registers 0x0000-0x0006
[+2s] Connecting to WiFi 'your-wifi-ssid'...
....
[+5s] WiFi connected, IP 192.168.1.42
[12:29:58] Time synced
[12:29:59] Registering device...
[12:30:00] Device registered (201)

Setup complete. Reading every 300 seconds...

[12:30:00] Burst reading 1/3... OK (M:89.7 T:27.4 EC:27 pH:5.5 N:0 P:1 K:5)
[12:30:10] Burst reading 2/3... OK (M:89.5 T:27.4 EC:28 pH:5.5 N:0 P:1 K:5)
[12:30:20] Burst reading 3/3... OK (M:89.6 T:27.3 EC:27 pH:5.5 N:0 P:1 K:4)
[12:30:20] Averaged: M:89.6 T:27.4 EC:27 pH:5.5 N:0 P:1 K:5 (3/3 valid)
[12:30:21] POST to Supabase... 201 Created
[12:30:21] Next reading in 300 seconds
```

With the probe in open air, moisture/EC/NPK near zero is normal. Insert the probe
fully into moist soil for meaningful readings.

## How it works

- **Boot:** connect WiFi → NTP sync (IST, `pool.ntp.org`) → upsert the device row
  so `sensor_readings` always has a valid foreign key.
- **Every `READING_INTERVAL`:** take `BURST_COUNT` Modbus reads `BURST_DELAY` apart,
  average only the valid ones, and POST the average.
- **Timestamps:** if NTP synced, an ISO 8601 UTC `reading_timestamp` is sent;
  otherwise the row falls back to the server-side default (`now()`).
- **Resilience:** WiFi is re-checked and reconnected before every POST. A failed
  POST prints the HTTP status and response body. If all burst reads fail, the POST
  cycle is skipped with a warning. The node never halts on error — it always
  continues to the next cycle.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `WiFi connection FAILED` | Wrong SSID/password (case-sensitive), or a 5 GHz network. ESP32 needs 2.4 GHz. |
| `TLS connect ... failed` | Clock not yet set (cert validity check fails) — let NTP sync first; or firewall blocking 443. |
| POST returns **401** | Wrong anon key, or RLS not allowing anon insert. Re-check the key and that the schema migration ran. |
| POST returns **404** | Wrong `SUPABASE_URL`, or the table doesn't exist. Confirm the schema migration created `devices` and `sensor_readings`. |
| POST returns **400** | Body/column mismatch — confirm the schema matches `001_initial_schema.sql`. The response body is printed to help. |
| Modbus reads fail (timeout / incomplete) | See the bench-test README: check 12V power, swap A/B wiring, confirm 4800 baud and DE/RE on GPIO4. |
| Readings post but timestamps look wrong | NTP didn't sync; check WiFi/DNS. The node still posts using server-side `now()`. |

For testing only, if you cannot get past the TLS handshake, you can temporarily
replace `secureClient.setCACert(GTS_ROOT_R4)` with `secureClient.setInsecure()`
to skip certificate validation. **Do not ship that** — it disables TLS trust.

## Relationship to the rest of CarbonReady

This is a **new standalone sketch**. It does not modify `bench_test.ino` or any
existing firmware. It targets its own Supabase project (see
`firmware/supabase/`), independent of the CarbonBazaar database. CarbonBazaar
reads this data through a REST bridge — it never shares a database or auth with
CarbonReady.
