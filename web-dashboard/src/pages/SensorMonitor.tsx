import { useCallback, useEffect, useState } from 'react';
import {
  getDevices,
  getLatestReadings,
  isConfigured,
  type CarbonReadyDevice,
  type CarbonReadyReading,
} from '../lib/carbonready';

// A device is considered "online" if seen within the last 30 minutes.
const ONLINE_WINDOW_MS = 30 * 60 * 1000;
// Auto-refresh cadence.
const REFRESH_INTERVAL_MS = 60 * 1000;

function fmt(value: number | null, digits = 1, suffix = ''): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '--';
  return `${value.toFixed(digits)}${suffix}`;
}

function fmtInt(value: number | null, suffix = ''): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '--';
  return `${Math.round(value)}${suffix}`;
}

// pH color banding: red at extremes, amber in warning zones, green when ideal.
function phColor(ph: number | null): string {
  if (ph === null) return 'var(--neutral-400)';
  if (ph < 4.5 || ph > 8.5) return 'var(--red-400)';
  if (ph < 5.5 || ph > 7.5) return 'var(--amber-400)';
  return 'var(--green-400)';
}

function moistureColor(m: number | null): string {
  if (m === null) return 'var(--neutral-400)';
  if (m < 30) return 'var(--red-400)';
  if (m > 70) return 'var(--blue-400)';
  return 'var(--green-400)';
}

function timeAgo(iso: string | null): string {
  if (!iso) return 'never';
  const diffMs = Date.now() - new Date(iso).getTime();
  const sec = Math.round(diffMs / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.round(hr / 24)}d ago`;
}

function isOnline(device: CarbonReadyDevice | null): boolean {
  if (!device?.last_seen_at) return false;
  return Date.now() - new Date(device.last_seen_at).getTime() < ONLINE_WINDOW_MS;
}

interface MetricProps {
  icon: string;
  label: string;
  value: string;
  color?: string;
  hint?: string;
}

function Metric({ icon, label, value, color, hint }: MetricProps) {
  return (
    <div className="sensor-reading">
      <div className="sensor-reading-label">
        {icon} {label}
      </div>
      <div className="sensor-reading-value" style={color ? { color } : undefined}>
        {value}
      </div>
      {hint && (
        <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--neutral-500)' }}>
          {hint}
        </div>
      )}
    </div>
  );
}

function SensorMonitor() {
  const [devices, setDevices] = useState<CarbonReadyDevice[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [readings, setReadings] = useState<CarbonReadyReading[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<number>(Date.now());

  const selectedDevice = devices.find((d) => d.device_id === selectedId) ?? null;
  const latest = readings[0] ?? null;

  // Load the device list once.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        if (!isConfigured()) {
          throw new Error(
            'CarbonReady Supabase not configured. Set VITE_CARBONREADY_SUPABASE_URL and ' +
              'VITE_CARBONREADY_SUPABASE_ANON_KEY in web-dashboard/.env, then restart the dev server.'
          );
        }
        const list = await getDevices();
        if (cancelled) return;
        setDevices(list);
        setSelectedId((prev) => prev ?? list[0]?.device_id ?? null);
        if (list.length === 0) setLoading(false);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load devices');
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const loadReadings = useCallback(
    async (deviceId: string, isManual: boolean) => {
      if (isManual) setRefreshing(true);
      try {
        const rows = await getLatestReadings(deviceId, 50);
        setReadings(rows);
        setError(null);
        setLastRefreshed(Date.now());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load readings');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    []
  );

  // Load readings when the selected device changes, then poll on an interval.
  useEffect(() => {
    if (!selectedId) return;
    loadReadings(selectedId, false);
    const timer = setInterval(() => loadReadings(selectedId, false), REFRESH_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [selectedId, loadReadings]);

  if (loading) {
    return (
      <>
        <div className="page-header">
          <h2>📡 Sensor Monitoring</h2>
          <span className="page-header-sub">Loading...</span>
        </div>
        <div className="container">
          <div className="loading">
            <div className="loading-spinner" />
            <div className="loading-text">Loading sensor data...</div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="page-header">
        <h2>📡 Sensor Monitoring</h2>
        <span className="page-header-sub">Live soil data from CarbonReady IoT nodes</span>
      </div>

      <div className="container">
        {error && (
          <div className="error" style={{ marginBottom: '20px' }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {devices.length === 0 && !error ? (
          <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>📡</div>
            <h3 style={{ marginBottom: '8px' }}>No sensor nodes deployed yet</h3>
            <p style={{ color: 'var(--neutral-500)' }}>
              CarbonReady IoT nodes will appear here once installed and posting data.
            </p>
          </div>
        ) : (
          <>
            {/* Device info + controls */}
            <div
              style={{
                background: 'var(--bg-elevated)',
                borderRadius: '12px',
                padding: '16px 20px',
                marginBottom: '24px',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    className="status-dot"
                    style={{
                      background: isOnline(selectedDevice)
                        ? 'var(--green-400)'
                        : 'var(--red-400)',
                      boxShadow: isOnline(selectedDevice)
                        ? '0 0 8px var(--green-400)'
                        : 'none',
                    }}
                  />
                  <span
                    style={{
                      fontSize: '13px',
                      fontWeight: 600,
                      color: isOnline(selectedDevice) ? 'var(--green-400)' : 'var(--red-400)',
                    }}
                  >
                    {isOnline(selectedDevice) ? 'Online' : 'Offline'}
                  </span>
                </div>

                {devices.length > 1 ? (
                  <select
                    value={selectedId ?? ''}
                    onChange={(e) => {
                      setSelectedId(e.target.value);
                      setLoading(true);
                    }}
                    style={{
                      background: 'var(--bg-base, #111)',
                      color: 'var(--neutral-200)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '6px',
                      padding: '6px 10px',
                      fontSize: '13px',
                    }}
                  >
                    {devices.map((d) => (
                      <option key={d.device_id} value={d.device_id}>
                        {d.name ? `${d.name} (${d.device_id})` : d.device_id}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span style={{ fontSize: '14px', fontWeight: 600 }}>
                    {selectedDevice?.name || selectedDevice?.device_id}
                  </span>
                )}

                <span
                  style={{
                    fontFamily: "'Fira Code', monospace",
                    fontSize: '12px',
                    color: 'var(--neutral-500)',
                  }}
                >
                  {selectedDevice?.device_id}
                </span>

                {(selectedDevice?.village || selectedDevice?.taluka) && (
                  <span style={{ fontSize: '12px', color: 'var(--neutral-400)' }}>
                    📍 {[selectedDevice?.village, selectedDevice?.taluka].filter(Boolean).join(', ')}
                  </span>
                )}

                {selectedDevice?.firmware_version && (
                  <span style={{ fontSize: '12px', color: 'var(--neutral-500)' }}>
                    fw {selectedDevice.firmware_version}
                  </span>
                )}

                <span style={{ fontSize: '12px', color: 'var(--neutral-500)' }}>
                  Last seen: {timeAgo(selectedDevice?.last_seen_at ?? null)}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                  Refreshed {timeAgo(new Date(lastRefreshed).toISOString())}
                </span>
                <button
                  onClick={() => selectedId && loadReadings(selectedId, true)}
                  disabled={refreshing}
                  style={{
                    padding: '6px 14px',
                    background: 'var(--green-600, #16a34a)',
                    border: 'none',
                    borderRadius: '6px',
                    color: 'white',
                    cursor: refreshing ? 'default' : 'pointer',
                    fontSize: '13px',
                    opacity: refreshing ? 0.6 : 1,
                  }}
                >
                  {refreshing ? 'Refreshing...' : '↻ Refresh'}
                </button>
              </div>
            </div>

            {/* Current readings */}
            <div className="card" style={{ marginBottom: '24px' }}>
              <h2 style={{ marginBottom: '4px' }}>Current Readings</h2>
              <div style={{ fontSize: '12px', color: 'var(--neutral-500)', marginBottom: '16px' }}>
                {latest
                  ? `As of ${new Date(latest.reading_timestamp).toLocaleString()} (${timeAgo(
                      latest.reading_timestamp
                    )})`
                  : 'No readings yet'}
              </div>

              {latest && (
                <div className="sensor-grid">
                  <Metric
                    icon="💧"
                    label="Moisture"
                    value={fmt(latest.moisture, 1, '%')}
                    color={moistureColor(latest.moisture)}
                  />
                  <Metric
                    icon="🌡️"
                    label="Temperature"
                    value={fmt(latest.temperature, 1, '°C')}
                  />
                  <Metric icon="⚡" label="EC" value={fmtInt(latest.ec, ' µS/cm')} />
                  <Metric
                    icon="🧪"
                    label="pH"
                    value={fmt(latest.ph, 1)}
                    color={phColor(latest.ph)}
                    hint={
                      latest.ph === null
                        ? undefined
                        : latest.ph < 5.5
                        ? 'Acidic'
                        : latest.ph > 7.5
                        ? 'Alkaline'
                        : 'Ideal range'
                    }
                  />
                  <Metric icon="🟢" label="Nitrogen (N)" value={fmtInt(latest.nitrogen, ' mg/kg')} />
                  <Metric
                    icon="🟠"
                    label="Phosphorus (P)"
                    value={fmtInt(latest.phosphorus, ' mg/kg')}
                  />
                  <Metric icon="🟣" label="Potassium (K)" value={fmtInt(latest.potassium, ' mg/kg')} />
                </div>
              )}
            </div>

            {/* Recent readings table */}
            <div className="card">
              <h2 style={{ marginBottom: '16px' }}>
                Recent Readings{' '}
                <span style={{ fontSize: '13px', fontWeight: 400, color: 'var(--neutral-500)' }}>
                  (last {readings.length})
                </span>
              </h2>

              {readings.length === 0 ? (
                <p style={{ color: 'var(--neutral-500)' }}>No readings recorded yet.</p>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table
                    style={{
                      width: '100%',
                      borderCollapse: 'collapse',
                      fontSize: '13px',
                    }}
                  >
                    <thead>
                      <tr style={{ textAlign: 'left', color: 'var(--neutral-400)' }}>
                        <th style={{ padding: '8px 10px' }}>Time</th>
                        <th style={{ padding: '8px 10px' }}>Moist %</th>
                        <th style={{ padding: '8px 10px' }}>Temp °C</th>
                        <th style={{ padding: '8px 10px' }}>EC</th>
                        <th style={{ padding: '8px 10px' }}>pH</th>
                        <th style={{ padding: '8px 10px' }}>N</th>
                        <th style={{ padding: '8px 10px' }}>P</th>
                        <th style={{ padding: '8px 10px' }}>K</th>
                      </tr>
                    </thead>
                    <tbody>
                      {readings.map((r, i) => (
                        <tr
                          key={r.id}
                          style={{
                            background: i % 2 === 0 ? 'transparent' : 'var(--bg-elevated)',
                            borderTop: '1px solid var(--border-subtle)',
                          }}
                        >
                          <td style={{ padding: '8px 10px', whiteSpace: 'nowrap' }}>
                            {new Date(r.reading_timestamp).toLocaleTimeString()}
                          </td>
                          <td style={{ padding: '8px 10px' }}>{fmt(r.moisture, 1)}</td>
                          <td style={{ padding: '8px 10px' }}>{fmt(r.temperature, 1)}</td>
                          <td style={{ padding: '8px 10px' }}>{fmtInt(r.ec)}</td>
                          <td style={{ padding: '8px 10px', color: phColor(r.ph) }}>{fmt(r.ph, 1)}</td>
                          <td style={{ padding: '8px 10px' }}>{fmtInt(r.nitrogen)}</td>
                          <td style={{ padding: '8px 10px' }}>{fmtInt(r.phosphorus)}</td>
                          <td style={{ padding: '8px 10px' }}>{fmtInt(r.potassium)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  );
}

export default SensorMonitor;
