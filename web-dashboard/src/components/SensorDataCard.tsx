import type { SensorData } from '../types';

interface Props {
  data: SensorData;
}

function SensorDataCard({ data }: Props) {
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
      if (value < 30) return '#dc3545';
      if (value > 70) return '#17a2b8';
      return '#28a745';
    }
    return 'var(--primary-green)';
  };

  return (
    <div className="card">
      <h2>📡 Latest Sensor Readings</h2>

      {isStale() && (
        <div className="stale-indicator">
          Sensor data is more than 24 hours old
        </div>
      )}

      <div className="sensor-grid">
        <div className="sensor-reading">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div className="sensor-reading-label">
              {getSensorIcon('moisture')} Soil Moisture
            </div>
          </div>
          <div className="sensor-reading-value" style={{ color: getSensorColor(data.readings.soilMoisture, 'moisture') }}>
            {data.readings.soilMoisture.toFixed(1)}%
          </div>
          <div style={{ marginTop: '8px' }}>
            <div style={{ 
              height: '6px', 
              background: 'var(--neutral-200)', 
              borderRadius: '3px',
              overflow: 'hidden'
            }}>
              <div style={{
                height: '100%',
                width: `${data.readings.soilMoisture}%`,
                background: getSensorColor(data.readings.soilMoisture, 'moisture'),
                transition: 'width 0.5s ease'
              }} />
            </div>
          </div>
        </div>

        <div className="sensor-reading">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div className="sensor-reading-label">
              {getSensorIcon('soilTemp')} Soil Temp
            </div>
          </div>
          <div className="sensor-reading-value">
            {data.readings.soilTemperature.toFixed(1)}°C
          </div>
          <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--neutral-600)' }}>
            Optimal: 20-25°C
          </div>
        </div>

        <div className="sensor-reading">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div className="sensor-reading-label">
              {getSensorIcon('airTemp')} Air Temp
            </div>
          </div>
          <div className="sensor-reading-value">
            {data.readings.airTemperature.toFixed(1)}°C
          </div>
          <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--neutral-600)' }}>
            Current conditions
          </div>
        </div>

        <div className="sensor-reading">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div className="sensor-reading-label">
              {getSensorIcon('humidity')} Humidity
            </div>
          </div>
          <div className="sensor-reading-value">
            {data.readings.humidity.toFixed(1)}%
          </div>
          <div style={{ marginTop: '8px' }}>
            <div style={{ 
              height: '6px', 
              background: 'var(--neutral-200)', 
              borderRadius: '3px',
              overflow: 'hidden'
            }}>
              <div style={{
                height: '100%',
                width: `${data.readings.humidity}%`,
                background: 'var(--sky-blue)',
                transition: 'width 0.5s ease'
              }} />
            </div>
          </div>
        </div>
      </div>

      <div className="breakdown" style={{ marginTop: '24px' }}>
        <h3>📋 Device Information</h3>
        <div className="breakdown-item">
          <span className="breakdown-label">🔌 Device ID</span>
          <span className="breakdown-value" style={{ fontFamily: 'monospace', fontSize: '13px' }}>
            {data.deviceId}
          </span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">✅ Validation Status</span>
          <span className="breakdown-value">
            <span style={{ 
              padding: '4px 10px', 
              background: data.validationStatus === 'valid' ? '#d4edda' : '#f8d7da',
              color: data.validationStatus === 'valid' ? '#155724' : '#721c24',
              borderRadius: '12px',
              fontSize: '12px',
              fontWeight: 600
            }}>
              {data.validationStatus}
            </span>
          </span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">🕐 Last Reading</span>
          <span className="breakdown-value" style={{ fontSize: '13px' }}>
            {new Date(data.timestamp).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Live Status Indicator */}
      <div style={{
        marginTop: '20px',
        padding: '12px 16px',
        background: 'linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%)',
        borderRadius: '10px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        border: '1px solid #b1dfbb'
      }}>
        <div style={{
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          background: '#28a745',
          boxShadow: '0 0 10px #28a745',
          animation: 'pulse 2s ease-in-out infinite'
        }} />
        <span style={{ fontSize: '13px', color: '#155724', fontWeight: 600 }}>
          Sensor Active • Receiving Data
        </span>
      </div>
    </div>
  );
}

export default SensorDataCard;
