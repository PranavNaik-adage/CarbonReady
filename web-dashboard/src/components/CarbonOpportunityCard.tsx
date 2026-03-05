import type { CarbonPosition, CarbonReadinessIndex } from '../types';

interface Props {
  carbonPosition: CarbonPosition;
  cri: CarbonReadinessIndex;
}

function CarbonOpportunityCard({ carbonPosition, cri }: Props) {
  // Calculate estimated sequestration in tCO2/year
  const sequestrationTons = (carbonPosition.annualSequestration / 1000).toFixed(2);
  
  // Determine carbon credit readiness based on CRI score and carbon position
  const getCreditReadiness = () => {
    const score = cri.carbonReadinessIndex.score;
    const isSink = carbonPosition.classification === 'Net Carbon Sink';
    const netPosition = carbonPosition.netCarbonPosition;
    
    if (isSink && score >= 70 && netPosition > 5000) {
      return { level: 'High', color: 'var(--green-400)', badge: 'excellent' };
    } else if (isSink && score >= 50 && netPosition > 2000) {
      return { level: 'Moderate', color: 'var(--amber-400)', badge: 'moderate' };
    } else {
      return { level: 'Low', color: 'var(--red-400)', badge: 'needs-improvement' };
    }
  };

  const creditReadiness = getCreditReadiness();

  const getReadinessMessage = () => {
    if (creditReadiness.level === 'High') {
      return 'Your farm meets the criteria for carbon credit programs. Consider registering for carbon markets.';
    } else if (creditReadiness.level === 'Moderate') {
      return 'Your farm shows potential for carbon credits. Improve practices to increase sequestration.';
    } else {
      return 'Focus on becoming carbon neutral first. Reduce emissions and improve soil carbon levels.';
    }
  };

  return (
    <div className="card">
      <h2>🚀 Carbon Opportunity</h2>

      <div className="breakdown" style={{ marginTop: '20px' }}>
        <div className="breakdown-item">
          <span className="breakdown-label">
            <span style={{ marginRight: '8px' }}>🌱</span>
            Estimated Sequestration
          </span>
          <span className="breakdown-value" style={{ color: 'var(--green-400)', fontSize: '16px' }}>
            {sequestrationTons} tCO₂/year
          </span>
        </div>

        <div className="breakdown-item">
          <span className="breakdown-label">
            <span style={{ marginRight: '8px' }}>📊</span>
            Carbon Credit Readiness
          </span>
          <span className={`badge ${creditReadiness.badge}`} style={{ fontSize: '12px' }}>
            {creditReadiness.level === 'High' ? '🟢 High' : 
             creditReadiness.level === 'Moderate' ? '🟡 Moderate' : '🔴 Low'}
          </span>
        </div>
      </div>

      {/* Disclaimer */}
      <div style={{
        marginTop: '16px',
        padding: '10px 12px',
        background: 'rgba(96, 165, 250, 0.06)',
        borderRadius: '8px',
        fontSize: '11px',
        color: 'var(--neutral-500)',
        fontStyle: 'italic',
        borderLeft: '2px solid var(--blue-400)'
      }}>
        Based on current farm data and modeling estimates
      </div>

      {/* Readiness Message */}
      <div style={{
        background: 'var(--bg-elevated)',
        padding: '14px 16px',
        borderRadius: '10px',
        marginTop: '20px',
        border: '1px solid var(--border-subtle)',
        fontSize: '13px',
        color: 'var(--neutral-600)',
        lineHeight: '1.6'
      }}>
        <div style={{ marginBottom: '8px', fontWeight: 600, color: 'var(--neutral-700)' }}>
          💡 Opportunity Assessment
        </div>
        {getReadinessMessage()}
      </div>

      {/* Potential Actions */}
      {creditReadiness.level !== 'High' && (
        <div style={{ marginTop: '20px' }}>
          <h3 style={{ fontSize: '13px', marginBottom: '12px', color: 'var(--neutral-700)' }}>
            🎯 Recommended Actions
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {carbonPosition.classification !== 'Net Carbon Sink' && (
              <div style={{
                padding: '10px 12px',
                background: 'rgba(251, 191, 36, 0.08)',
                borderRadius: '8px',
                fontSize: '12px',
                color: 'var(--neutral-600)',
                borderLeft: '3px solid var(--amber-400)'
              }}>
                <strong>Reduce Emissions:</strong> Optimize fertilizer use and irrigation practices
              </div>
            )}
            {cri.socTrend.status !== 'Improving' && (
              <div style={{
                padding: '10px 12px',
                background: 'rgba(52, 211, 153, 0.08)',
                borderRadius: '8px',
                fontSize: '12px',
                color: 'var(--neutral-600)',
                borderLeft: '3px solid var(--green-400)'
              }}>
                <strong>Improve Soil Health:</strong> Add organic matter and reduce tillage
              </div>
            )}
            <div style={{
              padding: '10px 12px',
              background: 'rgba(96, 165, 250, 0.08)',
              borderRadius: '8px',
              fontSize: '12px',
              color: 'var(--neutral-600)',
              borderLeft: '3px solid var(--blue-400)'
            }}>
              <strong>Monitor Progress:</strong> Continue tracking with sensors for verification
            </div>
          </div>
        </div>
      )}

      {creditReadiness.level === 'High' && (
        <div style={{
          marginTop: '20px',
          padding: '16px',
          background: 'rgba(52, 211, 153, 0.08)',
          borderRadius: '12px',
          border: '1px solid rgba(52, 211, 153, 0.2)'
        }}>
          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--green-400)', marginBottom: '8px' }}>
            ✅ Ready for Carbon Markets
          </div>
          <div style={{ fontSize: '12px', color: 'var(--neutral-600)', lineHeight: '1.6' }}>
            Your farm qualifies for carbon credit programs. Contact carbon market registries to begin the certification process.
          </div>
        </div>
      )}
    </div>
  );
}

export default CarbonOpportunityCard;
