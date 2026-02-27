import type { CarbonReadinessIndex } from '../types';

interface Props {
  data: CarbonReadinessIndex;
}

function CRICard({ data }: Props) {
  const { carbonReadinessIndex, socTrend } = data;

  const getClassificationBadge = (classification: string) => {
    const classMap: Record<string, string> = {
      'Excellent': 'badge excellent',
      'Moderate': 'badge moderate',
      'Needs Improvement': 'badge needs-improvement'
    };
    return classMap[classification] || 'badge';
  };

  const getSOCBadge = (status: string) => {
    const classMap: Record<string, string> = {
      'Improving': 'badge improving',
      'Stable': 'badge stable',
      'Declining': 'badge declining',
      'Insufficient Data': 'badge moderate'
    };
    return classMap[status] || 'badge';
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return '#28a745';
    if (score >= 40) return '#ffc107';
    return '#dc3545';
  };

  return (
    <div className="card">
      <h2>⭐ Carbon Readiness Index</h2>

      {/* Circular Progress Indicator */}
      <div style={{ display: 'flex', justifyContent: 'center', margin: '24px 0' }}>
        <div style={{ position: 'relative', width: '180px', height: '180px' }}>
          <svg width="180" height="180" style={{ transform: 'rotate(-90deg)' }}>
            {/* Background circle */}
            <circle
              cx="90"
              cy="90"
              r="75"
              fill="none"
              stroke="var(--neutral-200)"
              strokeWidth="15"
            />
            {/* Progress circle */}
            <circle
              cx="90"
              cy="90"
              r="75"
              fill="none"
              stroke={getScoreColor(carbonReadinessIndex.score)}
              strokeWidth="15"
              strokeDasharray={`${(carbonReadinessIndex.score / 100) * 471} 471`}
              strokeLinecap="round"
              style={{ transition: 'stroke-dasharray 1s ease' }}
            />
          </svg>
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center'
          }}>
            <div style={{ 
              fontSize: '42px', 
              fontWeight: 700, 
              color: getScoreColor(carbonReadinessIndex.score),
              lineHeight: 1
            }}>
              {carbonReadinessIndex.score.toFixed(1)}
            </div>
            <div style={{ fontSize: '14px', color: 'var(--neutral-600)', marginTop: '4px' }}>
              out of 100
            </div>
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <span className={getClassificationBadge(carbonReadinessIndex.classification)}>
          {carbonReadinessIndex.classification}
        </span>
      </div>

      <div className="component-breakdown">
        <h3>📈 Component Breakdown</h3>
        
        {/* Net Carbon Position Component */}
        <div className="component-item">
          <div className="component-header">
            <span className="component-name">🌍 Net Carbon Position</span>
            <span className="component-score">
              {carbonReadinessIndex.components.netCarbonPosition.score.toFixed(1)}
            </span>
          </div>
          <div style={{ marginTop: '8px' }}>
            <div style={{ 
              height: '8px', 
              background: 'var(--neutral-200)', 
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                height: '100%',
                width: `${carbonReadinessIndex.components.netCarbonPosition.score}%`,
                background: 'linear-gradient(90deg, var(--primary-green), var(--accent-green))',
                transition: 'width 1s ease'
              }} />
            </div>
          </div>
          <div className="component-details" style={{ marginTop: '8px' }}>
            Weight: {(carbonReadinessIndex.components.netCarbonPosition.weight * 100).toFixed(0)}% • 
            Contribution: {carbonReadinessIndex.components.netCarbonPosition.contribution.toFixed(1)} points
          </div>
        </div>

        {/* SOC Trend Component */}
        <div className="component-item">
          <div className="component-header">
            <span className="component-name">🌱 Soil Organic Carbon</span>
            <span className="component-score">
              {carbonReadinessIndex.components.socTrend.score.toFixed(1)}
            </span>
          </div>
          <div style={{ marginTop: '8px' }}>
            <div style={{ 
              height: '8px', 
              background: 'var(--neutral-200)', 
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                height: '100%',
                width: `${carbonReadinessIndex.components.socTrend.score}%`,
                background: 'linear-gradient(90deg, var(--primary-green), var(--accent-green))',
                transition: 'width 1s ease'
              }} />
            </div>
          </div>
          <div className="component-details" style={{ marginTop: '8px' }}>
            Weight: {(carbonReadinessIndex.components.socTrend.weight * 100).toFixed(0)}% • 
            Contribution: {carbonReadinessIndex.components.socTrend.contribution.toFixed(1)} points
          </div>
        </div>

        {/* Management Practices Component */}
        <div className="component-item">
          <div className="component-header">
            <span className="component-name">🚜 Management Practices</span>
            <span className="component-score">
              {carbonReadinessIndex.components.managementPractices.score.toFixed(1)}
            </span>
          </div>
          <div style={{ marginTop: '8px' }}>
            <div style={{ 
              height: '8px', 
              background: 'var(--neutral-200)', 
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                height: '100%',
                width: `${carbonReadinessIndex.components.managementPractices.score}%`,
                background: 'linear-gradient(90deg, var(--primary-green), var(--accent-green))',
                transition: 'width 1s ease'
              }} />
            </div>
          </div>
          <div className="component-details" style={{ marginTop: '8px' }}>
            Weight: {(carbonReadinessIndex.components.managementPractices.weight * 100).toFixed(0)}% • 
            Contribution: {carbonReadinessIndex.components.managementPractices.contribution.toFixed(1)} points
          </div>
        </div>
      </div>

      <div className="breakdown" style={{ marginTop: '20px' }}>
        <h3>🌾 SOC Trend Analysis</h3>
        <div className="breakdown-item">
          <span className="breakdown-label">Status</span>
          <span className={getSOCBadge(socTrend.status)}>
            {socTrend.status}
          </span>
        </div>
        {socTrend.score !== undefined && (
          <div className="breakdown-item">
            <span className="breakdown-label">SOC Proxy Score</span>
            <span className="breakdown-value">
              {socTrend.score.toFixed(3)}
            </span>
          </div>
        )}
        {socTrend.dataSpanDays !== undefined && (
          <div className="breakdown-item">
            <span className="breakdown-label">Data Span</span>
            <span className="breakdown-value">
              {socTrend.dataSpanDays} days
            </span>
          </div>
        )}
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
        <span>ℹ️</span>
        <span>
          Scoring Logic: {carbonReadinessIndex.scoringLogicVersion} • 
          Calculated: {new Date(carbonReadinessIndex.calculatedAt).toLocaleString()}
        </span>
      </div>
    </div>
  );
}

export default CRICard;
