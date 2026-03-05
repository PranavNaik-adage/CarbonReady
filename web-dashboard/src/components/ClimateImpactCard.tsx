import type { CarbonPosition } from '../types';

interface Props {
  carbonPosition: CarbonPosition;
}

function ClimateImpactCard({ carbonPosition }: Props) {
  // Calculations
  const annualSequestrationTonnes = carbonPosition.annualSequestration / 1000;
  const fiveYearImpact = annualSequestrationTonnes * 5;
  const carsEquivalent = annualSequestrationTonnes / 4.6;
  const treesEquivalent = (annualSequestrationTonnes * 1000) / 21;

  return (
    <div className="card">
      <h2>🌍 Climate Impact</h2>
      
      <div style={{
        marginTop: '20px',
        fontSize: '12px',
        color: 'var(--neutral-500)',
        fontStyle: 'italic',
        textAlign: 'center',
        marginBottom: '20px'
      }}>
        Understanding your farm's positive impact on the environment
      </div>

      <div className="breakdown">
        <div className="breakdown-item">
          <span className="breakdown-label">
            <span style={{ marginRight: '8px' }}>🌱</span>
            Annual Carbon Removal
          </span>
          <span className="breakdown-value" style={{ color: 'var(--green-400)', fontSize: '16px' }}>
            {annualSequestrationTonnes.toFixed(2)} tonnes CO₂/year
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
          Carbon your farm removes from the atmosphere annually
        </div>

        <div className="breakdown-item">
          <span className="breakdown-label">
            <span style={{ marginRight: '8px' }}>📅</span>
            5-Year Climate Impact
          </span>
          <span className="breakdown-value" style={{ color: 'var(--teal-400)', fontSize: '16px' }}>
            {fiveYearImpact.toFixed(2)} tonnes CO₂
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
          Total carbon removal over five years at current rate
        </div>
      </div>

      {/* Equivalents Section */}
      <div style={{ marginTop: '24px' }}>
        <h3 style={{ 
          fontSize: '14px', 
          marginBottom: '16px', 
          color: 'var(--neutral-700)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          💡 Real-World Equivalents
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          {/* Trees Equivalent */}
          <div style={{
            padding: '16px',
            background: 'var(--bg-elevated)',
            borderRadius: '12px',
            border: '1px solid var(--border-subtle)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '32px', marginBottom: '8px' }}>🌳</div>
            <div style={{ 
              fontSize: '24px', 
              fontWeight: 800, 
              color: 'var(--green-400)',
              lineHeight: 1,
              marginBottom: '6px'
            }}>
              {treesEquivalent.toFixed(0)}
            </div>
            <div style={{ 
              fontSize: '11px', 
              color: 'var(--neutral-500)',
              fontWeight: 500
            }}>
              Equivalent Trees
            </div>
            <div style={{
              fontSize: '10px',
              color: 'var(--neutral-400)',
              marginTop: '6px',
              fontStyle: 'italic'
            }}>
              Trees needed to match your annual carbon removal
            </div>
          </div>

          {/* Cars Equivalent */}
          <div style={{
            padding: '16px',
            background: 'var(--bg-elevated)',
            borderRadius: '12px',
            border: '1px solid var(--border-subtle)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '32px', marginBottom: '8px' }}>🚗</div>
            <div style={{ 
              fontSize: '24px', 
              fontWeight: 800, 
              color: 'var(--blue-400)',
              lineHeight: 1,
              marginBottom: '6px'
            }}>
              {carsEquivalent.toFixed(1)}
            </div>
            <div style={{ 
              fontSize: '11px', 
              color: 'var(--neutral-500)',
              fontWeight: 500
            }}>
              Cars Off the Road
            </div>
            <div style={{
              fontSize: '10px',
              color: 'var(--neutral-400)',
              marginTop: '6px',
              fontStyle: 'italic'
            }}>
              Annual car emissions offset by your farm
            </div>
          </div>
        </div>
      </div>

      {/* Impact Message */}
      <div style={{
        marginTop: '20px',
        padding: '14px 16px',
        background: 'rgba(52, 211, 153, 0.08)',
        borderRadius: '10px',
        border: '1px solid rgba(52, 211, 153, 0.2)',
        fontSize: '12px',
        color: 'var(--neutral-600)',
        lineHeight: '1.6',
        textAlign: 'center'
      }}>
        <strong style={{ color: 'var(--green-400)' }}>🎉 Great work!</strong> Your sustainable farming practices are making a measurable difference in fighting climate change.
      </div>

      {/* Disclaimer */}
      <div style={{
        marginTop: '12px',
        padding: '10px 12px',
        background: 'rgba(96, 165, 250, 0.06)',
        borderRadius: '8px',
        fontSize: '10px',
        color: 'var(--neutral-500)',
        fontStyle: 'italic',
        borderLeft: '2px solid var(--blue-400)'
      }}>
        Impact calculated using IPCC emission equivalence factors. Equivalents based on standard emission factors: 4.6 tonnes CO₂/car/year, 21 kg CO₂/tree/year
      </div>
    </div>
  );
}

export default ClimateImpactCard;
