import { useState } from 'react';
import type { CarbonPosition } from '../types';

interface Props {
  data: CarbonPosition;
}

function CarbonPositionCard({ data }: Props) {
  const [expanded, setExpanded] = useState(false);

  // Safety checks
  if (!data || !data.emissions) {
    return (
      <div className="card">
        <h2>🌍 Net Carbon Position</h2>
        <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
          No carbon position data available
        </div>
      </div>
    );
  }

  const getBadgeClass = (classification: string) => {
    return classification === 'Net Carbon Sink' ? 'badge sink' : 'badge source';
  };

  const isSink = data.classification === 'Net Carbon Sink';
  const totalEmissions = data.emissions?.totalEmissions || 0;
  const annualSequestration = data.annualSequestration || 0;
  const sequestrationPercent = totalEmissions > 0
    ? (annualSequestration / (annualSequestration + totalEmissions)) * 100
    : 100;

  return (
    <div className="card">
      <div className="card-header-toggle" onClick={() => setExpanded(!expanded)}>
        <h2>🌍 Net Carbon Position</h2>
        <span className={`card-chevron ${expanded ? 'expanded' : ''}`}>▼</span>
      </div>

      {/* Mobile Summary — key metric when collapsed */}
      <div className={`card-summary ${expanded ? 'hidden' : ''}`}>
        <div className="card-summary-row">
          <span className="card-summary-label">Net Balance</span>
          <span className="card-summary-value" style={{ color: isSink ? 'var(--green-400)' : 'var(--red-400)' }}>
            {isSink ? '+' : ''}{data.netCarbonPosition.toFixed(0)} <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--neutral-400)' }}>kg CO₂e/yr</span>
          </span>
        </div>
        <div className="card-summary-row">
          <span className="card-summary-label">Status</span>
          <span className={getBadgeClass(data.classification)} style={{ fontSize: '11px' }}>
            {data.classification}
          </span>
        </div>
        <span className="card-expand-hint">Tap to see details</span>
      </div>

      {/* Full Details */}
      <div className={`card-details ${expanded ? 'expanded' : 'collapsed'}`} style={{ maxHeight: expanded ? '2000px' : undefined }}>
        <div className="card-header-divider" />

        {data.isStale && (
          <div className="stale-indicator">
            Data is more than 24 hours old
          </div>
        )}

        <div className="metric">
          <div className="metric-label">Net Carbon Balance</div>
          <div>
            <span className="metric-value" style={{ color: isSink ? 'var(--green-400)' : 'var(--red-400)' }}>
              {isSink ? '+' : ''}{data.netCarbonPosition.toFixed(2)}
              <span className="metric-unit">{data.unit}</span>
            </span>
          </div>
          <div style={{ marginTop: '12px' }}>
            <span className={getBadgeClass(data.classification)}>
              {data.classification === 'Net Carbon Sink' ? '🟢 Excellent' : '🔴 Needs Improvement'}
            </span>
          </div>
          {/* Simple explanation */}
          <div style={{
            marginTop: '12px',
            fontSize: '12px',
            color: 'var(--neutral-500)',
            lineHeight: '1.5',
            fontStyle: 'italic'
          }}>
            {isSink 
              ? '✓ Your farm removes more CO₂ from the air than it produces' 
              : '⚠ Your farm produces more CO₂ than it removes'}
          </div>
        </div>

        {/* Visual Balance Bar */}
        <div style={{ margin: '24px 0' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: '10px',
            fontSize: '12px',
            fontWeight: 600,
            letterSpacing: '0.5px',
            textTransform: 'uppercase' as const
          }}>
            <span style={{ color: 'var(--green-400)' }}>Sequestration</span>
            <span style={{ color: 'var(--red-400)' }}>Emissions</span>
          </div>
          <div style={{
            height: '28px',
            background: `linear-gradient(90deg, var(--green-500) 0%, var(--green-500) ${sequestrationPercent}%, var(--red-500) ${sequestrationPercent}%, var(--red-500) 100%)`,
            borderRadius: '14px',
            position: 'relative',
            boxShadow: 'inset 0 2px 6px rgba(0,0,0,0.3)',
            overflow: 'hidden'
          }}>
            <div style={{
              position: 'absolute',
              left: sequestrationPercent + '%',
              top: '50%',
              transform: 'translate(-50%, -50%)',
              width: '3px',
              height: '100%',
              background: 'rgba(255,255,255,0.8)',
              boxShadow: '0 0 10px rgba(255,255,255,0.5)'
            }} />
          </div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '8px',
            fontSize: '13px',
            fontWeight: 700
          }}>
            <span style={{ color: 'var(--green-400)' }}>+{annualSequestration.toFixed(0)}</span>
            <span style={{ color: 'var(--red-400)' }}>-{totalEmissions.toFixed(0)}</span>
          </div>
        </div>

        <div className="breakdown">
          <h3>📊 Detailed Breakdown</h3>
          <div className="breakdown-item">
            <span className="breakdown-label">🌱 Annual Sequestration</span>
            <span className="breakdown-value" style={{ color: 'var(--green-400)' }}>
              +{annualSequestration.toFixed(2)} kg CO₂e/yr
            </span>
          </div>
          <div style={{
            fontSize: '11px',
            color: 'var(--neutral-500)',
            marginTop: '4px',
            marginBottom: '12px',
            fontStyle: 'italic',
            paddingLeft: '28px'
          }}>
            Carbon your farm removes from the atmosphere each year
          </div>
          
          <div className="breakdown-item">
            <span className="breakdown-label">💨 Total Emissions</span>
            <span className="breakdown-value" style={{ color: 'var(--red-400)' }}>
              -{totalEmissions.toFixed(2)} kg CO₂e/yr
            </span>
          </div>
          <div style={{
            fontSize: '11px',
            color: 'var(--neutral-500)',
            marginTop: '4px',
            marginBottom: '12px',
            fontStyle: 'italic',
            paddingLeft: '28px'
          }}>
            Carbon released from farming activities
          </div>
          
          <div className="breakdown-item" style={{ paddingLeft: '20px' }}>
            <span className="breakdown-label" style={{ fontSize: '12px' }}>• Fertilizer</span>
            <span className="breakdown-value" style={{ fontSize: '12px' }}>
              {(data.emissions?.fertilizerEmissions || 0).toFixed(2)}
            </span>
          </div>
          <div className="breakdown-item" style={{ paddingLeft: '20px' }}>
            <span className="breakdown-label" style={{ fontSize: '12px' }}>• Irrigation</span>
            <span className="breakdown-value" style={{ fontSize: '12px' }}>
              {(data.emissions?.irrigationEmissions || 0).toFixed(2)}
            </span>
          </div>
        </div>

        <div className="breakdown" style={{ marginTop: '16px' }}>
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

        <div className="info-footer">
          <span>🕐</span>
          <span>Last calculated: {new Date(data.calculatedAt).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}

export default CarbonPositionCard;
