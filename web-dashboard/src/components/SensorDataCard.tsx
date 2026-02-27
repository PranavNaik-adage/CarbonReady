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

  return (
    <div className="card">
      <h2>Latest Sensor Readings</h2>

      {isStale() && (
        <div className="stale-indicator">
          ⚠️ Sensor data is more than 24 hours old
        </div>
      )}

      <div className="sensor-grid">
        <div className="sensor-reading">
          <div className="sensor-reading-label">Soil Moisture</div>
          <div className="sensor-reading-value">
            {data.readings.soilMoisture.toFixed(1)}%
          </div>
        </div>

        <div className="sensor-reading">
          <div className="sensor-reading-label">Soil Temperature</div>
          <div className="sensor-reading-value">
            {data.readings.soilTemperature.toFixed(1)}°C
          </div>
        </div>

        <div className="sensor-reading">
          <div className="sensor-reading-label">Air Temperature</div>
          <div className="sensor-reading-value">
            {data.readings.airTemperature.toFixed(1)}°C
          </div>
        </div>

        <div className="sensor-reading">
          <div className="sensor-reading-label">Humidity</div>
          <div className="sensor-reading-value">
            {data.readings.humidity.toFixed(1)}%
          </div>
        </div>
      </div>

      <div className="breakdown" style={{ marginTop: '20px' }}>
        <div className="breakdown-item">
          <span className="breakdown-label">Device ID</span>
          <span className="breakdown-value">{data.deviceId}</span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">Validation Status</span>
          <span className="breakdown-value">{data.validationStatus}</span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">Last Reading</span>
          <span className="breakdown-value">
            {new Date(data.timestamp).toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}

export default SensorDataCard;
