import { useState } from 'react';
import type { SensorData } from '../types';

interface Props {
  data: SensorData;
}

function SensorDataCard({ data }: Props) {
  const [expanded, setExpanded] = useState(false);

  const isStale = () => {
    const timestamp = new Date(data.timestamp);
    const now = new Date();
    const hoursDiff = (now.getTime() - timestamp.getTime()) / (1000 * 60 * 60);
    return hoursDiff > 24;
  };

  const getSensorIcon = (type: string) => {
    const icons: Record<string, string> = {
      moisture: '💧',
      soilTemp: '🌡️',
      airTemp: '🌤️',
      humidity: '💨'
    };
    return icons[type] || '📊';
  };

  const getSensorColor = (value: number, type: string) => {
    if (type === 'moisture') {
      if (value < 30) return 'var(--red-400)';
      if (value > 70) return 'var(--blue-400)';
      return 'var(--green-400)';
    }
    return 'var(--green-400)';
  };

  return (
    <div className="card">
      <div className="card-header-toggle" onClick={() => setExpanded(!expanded)}>
        <h2>📡 Latest Sensor Readings</h2>
        <span className={`card-chevron ${expanded ? 'expanded' : ''}`}>▼</span>
      </div>

      {/* Mobile Summary — key sensor values when collapsed */}
      <div className={`card-summary ${expanded ? 'hidden' : ''}`}>
        <div className="card-summary-row">
          <span className="card-summary-label">💧 Moisture</span>
          <span className="card-summary-value" style={{ color: getSensorColor(data.readings.soilMoisture, 'moisture') }}>
            {data.readings.soilMoisture.toFixed(1)}%
          </span>
        </div>
        <div className="card-summary-row">
          <span className="card-summary-label">🌡️ Soil Temp</span>
          <span className="card-summary-value">
            {data.readings.soilTemperature.toFixed(1)}°C
          </span>
        </div>
        <div className="card-summary-row">
          <span className="card-summary-label">🌤️ Air Temp</span>
          <span className="card-summary-value">
            {data.readings.airTemperature.toFixed(1)}°C
          </span>
        </div>
        <div className="card-summary-row">
          <span className="card-summary-label">💨 Humidity</span>
          <span className="card-summary-value" style={{ color: 'var(--blue-400)' }}>
            {data.readings.humidity.toFixed(1)}%
          </span>
        </div>
        <span className="card-expand-hint">Tap to see details</span>
      </div>

      {/* Full Details */}
      <div className={`card-details ${expanded ? 'expanded' : 'collapsed'}`} style={{ maxHeight: expanded ? '2000px' : undefined }}>
        <div className="card-header-divider" />

        {isStale() && (
          <div className="stale-indicator">
            Sensor data is more than 24 hours old
          </div>
        )}

        <div className="sensor-grid">
          <div className="sensor-reading">
            <div className="sensor-reading-label">
              {getSensorIcon('moisture')} Soil Moisture
            </div>
            <div className="sensor-reading-value" style={{ color: getSensorColor(data.readings.soilMoisture, 'moisture') }}>
              {data.readings.soilMoisture.toFixed(1)}%
            </div>
            <div className="progress-bar-track" style={{ marginTop: '10px' }}>
              <div
                className="progress-bar-fill"
                style={{
                  width: `${data.readings.soilMoisture}%`,
                  background: getSensorColor(data.readings.soilMoisture, 'moisture')
                }}
              />
            </div>
          </div>

          <div className="sensor-reading">
            <div className="sensor-reading-label">
              {getSensorIcon('soilTemp')} Soil Temp
            </div>
            <div className="sensor-reading-value">
              {data.readings.soilTemperature.toFixed(1)}°C
            </div>
            <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--neutral-400)', fontWeight: 500 }}>
              Optimal: 20–25°C
            </div>
          </div>

          <div className="sensor-reading">
            <div className="sensor-reading-label">
              {getSensorIcon('airTemp')} Air Temp
            </div>
            <div className="sensor-reading-value">
              {data.readings.airTemperature.toFixed(1)}°C
            </div>
            <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--neutral-400)', fontWeight: 500 }}>
              Current conditions
            </div>
          </div>

          <div className="sensor-reading">
            <div className="sensor-reading-label">
              {getSensorIcon('humidity')} Humidity
            </div>
            <div className="sensor-reading-value" style={{ color: 'var(--blue-400)' }}>
              {data.readings.humidity.toFixed(1)}%
            </div>
            <div className="progress-bar-track" style={{ marginTop: '10px' }}>
              <div
                className="progress-bar-fill"
                style={{
                  width: `${data.readings.humidity}%`,
                  background: 'var(--blue-400)',
                  boxShadow: '0 0 10px rgba(96, 165, 250, 0.3)'
                }}
              />
            </div>
          </div>
        </div>

        <div className="breakdown" style={{ marginTop: '24px' }}>
          <h3>📋 Device Information</h3>
          <div className="breakdown-item">
            <span className="breakdown-label">🔌 Device ID</span>
            <span className="breakdown-value" style={{ fontFamily: "'Fira Code', monospace", fontSize: '12px' }}>
              {data.deviceId}
            </span>
          </div>
          <div className="breakdown-item">
            <span className="breakdown-label">✅ Validation</span>
            <span className="breakdown-value">
              <span className={data.validationStatus === 'valid' ? 'badge excellent' : 'badge needs-improvement'} style={{ marginLeft: 0, fontSize: '11px' }}>
                {data.validationStatus}
              </span>
            </span>
          </div>
          <div className="breakdown-item">
            <span className="breakdown-label">🕐 Last Reading</span>
            <span className="breakdown-value" style={{ fontSize: '12px' }}>
              {new Date(data.timestamp).toLocaleString()}
            </span>
          </div>
        </div>

        <div className="live-status">
          <div className="live-dot" />
          <span className="live-text">
            Sensor Active • Receiving Data
          </span>
        </div>
      </div>
    </div>
  );
}

export default SensorDataCard;
