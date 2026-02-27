import type { CarbonPosition } from '../types';

interface Props {
  data: CarbonPosition;
}

function CarbonPositionCard({ data }: Props) {
  const getBadgeClass = (classification: string) => {
    return classification === 'Net Carbon Sink' ? 'badge sink' : 'badge source';
  };

  const isSink = data.classification === 'Net Carbon Sink';
  const sequestrationPercent = (data.annualSequestration / (data.annualSequestration + data.emissions.totalEmissions)) * 100;

  return (
    <div className="card">
      <h2>🌍 Net Carbon Position</h2>
      
      {data.isStale && (
        <div className="stale-indicator">
          Data is more than 24 hours old
        </div>
      )}

      <div className="metric">
        <div className="metric-label">Net Carbon Balance</div>
        <div>
          <span className="metric-value" style={{ color: isSink ? '#28a745' : '#dc3545' }}>
            {isSink ? '+' : ''}{data.netCarbonPosition.toFixed(2)}
          </span>
          <span className="metric-unit">{data.unit}</span>
        </div>
        <span className={getBadgeClass(data.classification)}>
          {data.classification}
        </span>
      </div>

      {/* Visual Balance Bar */}
      <div style={{ margin: '24px 0' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: '8px',
          fontSize: '13px',
          fontWeight: 600
        }}>
          <span style={{ color: '#28a745' }}>Sequestration</span>
          <span style={{ color: '#dc3545' }}>Emissions</span>
        </div>
        <div style={{ 
          height: '32px', 
          background: 'linear-gradient(90deg, #28a745 0%, #28a745 ' + sequestrationPercent + '%, #dc3545 ' + sequestrationPercent + '%, #dc3545 100%)',
          borderRadius: '16px',
          position: 'relative',
          boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)',
          overflow: 'hidden'
        }}>
          <div style={{
            position: 'absolute',
            left: sequestrationPercent + '%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            width: '3px',
            height: '100%',
            background: 'white',
            boxShadow: '0 0 8px rgba(0,0,0,0.3)'
          }} />
        </div>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginTop: '8px',
          fontSize: '14px',
          fontWeight: 600
        }}>
          <span style={{ color: '#28a745' }}>+{data.annualSequestration.toFixed(0)}</span>
          <span style={{ color: '#dc3545' }}>-{data.emissions.totalEmissions.toFixed(0)}</span>
        </div>
      </div>

      <div className="breakdown">
        <h3>📊 Detailed Breakdown</h3>
        <div className="breakdown-item">
          <span className="breakdown-label">🌱 Annual Sequestration</span>
          <span className="breakdown-value" style={{ color: '#28a745' }}>
            +{data.annualSequestration.toFixed(2)} kg CO₂e/year
          </span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">💨 Total Emissions</span>
          <span className="breakdown-value" style={{ color: '#dc3545' }}>
            -{data.emissions.totalEmissions.toFixed(2)} kg CO₂e/year
          </span>
        </div>
        <div className="breakdown-item" style={{ paddingLeft: '20px', fontSize: '13px' }}>
          <span className="breakdown-label">• Fertilizer</span>
          <span className="breakdown-value" style={{ fontSize: '13px' }}>
            {data.emissions.fertilizerEmissions.toFixed(2)} kg CO₂e/year
          </span>
        </div>
        <div className="breakdown-item" style={{ paddingLeft: '20px', fontSize: '13px' }}>
          <span className="breakdown-label">• Irrigation</span>
          <span className="breakdown-value" style={{ fontSize: '13px' }}>
            {data.emissions.irrigationEmissions.toFixed(2)} kg CO₂e/year
          </span>
        </div>
      </div>

      <div className="breakdown" style={{ marginTop: '20px' }}>
        <h3>🏦 Carbon Stock</h3>
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

      <div style={{ 
        marginTop: '20px', 
        padding: '12px', 
        background: 'var(--neutral-50)', 
        borderRadius: '8px',
        fontSize: '12px', 
        color: 'var(--neutral-600)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <span>🕐</span>
        <span>Last calculated: {new Date(data.calculatedAt).toLocaleString()}</span>
      </div>
    </div>
  );
}

export default CarbonPositionCard;
