import type { CarbonPosition } from '../types';

interface Props {
  data: CarbonPosition;
}

function CarbonPositionCard({ data }: Props) {
  const getBadgeClass = (classification: string) => {
    return classification === 'Net Carbon Sink' ? 'badge sink' : 'badge source';
  };

  return (
    <div className="card">
      <h2>Net Carbon Position</h2>
      
      {data.isStale && (
        <div className="stale-indicator">
          ⚠️ Data is more than 24 hours old
        </div>
      )}

      <div className="metric">
        <div className="metric-label">Net Carbon Position</div>
        <div>
          <span className="metric-value">
            {data.netCarbonPosition.toFixed(2)}
          </span>
          <span className="metric-unit">{data.unit}</span>
          <span className={getBadgeClass(data.classification)}>
            {data.classification}
          </span>
        </div>
      </div>

      <div className="breakdown">
        <h3>Emissions vs Sequestration Breakdown</h3>
        <div className="breakdown-item">
          <span className="breakdown-label">Annual Sequestration</span>
          <span className="breakdown-value" style={{ color: '#28a745' }}>
            +{data.annualSequestration.toFixed(2)} kg CO₂e/year
          </span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">Total Emissions</span>
          <span className="breakdown-value" style={{ color: '#dc3545' }}>
            -{data.emissions.totalEmissions.toFixed(2)} kg CO₂e/year
          </span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">Fertilizer Emissions</span>
          <span className="breakdown-value">
            {data.emissions.fertilizerEmissions.toFixed(2)} kg CO₂e/year
          </span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">Irrigation Emissions</span>
          <span className="breakdown-value">
            {data.emissions.irrigationEmissions.toFixed(2)} kg CO₂e/year
          </span>
        </div>
      </div>

      <div className="breakdown" style={{ marginTop: '20px' }}>
        <h3>Carbon Stock</h3>
        <div className="breakdown-item">
          <span className="breakdown-label">Total Carbon Stock</span>
          <span className="breakdown-value">
            {data.carbonStock.toFixed(2)} kg C
          </span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">CO₂ Equivalent Stock</span>
          <span className="breakdown-value">
            {data.co2EquivalentStock.toFixed(2)} kg CO₂e
          </span>
        </div>
      </div>

      <div style={{ marginTop: '15px', fontSize: '12px', color: '#999' }}>
        Last calculated: {new Date(data.calculatedAt).toLocaleString()}
      </div>
    </div>
  );
}

export default CarbonPositionCard;
