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
    if (score >= 70) return 'var(--green-400)';
    if (score >= 40) return 'var(--amber-400)';
    return 'var(--red-400)';
  };

  const circumference = 2 * Math.PI * 75;
  const strokeDashoffset = circumference - (carbonReadinessIndex.score / 100) * circumference;

  return (
    <div className="card">
      <h2>⭐ Carbon Readiness Index</h2>

      {/* Circular Progress Indicator */}
      <div style={{ display: 'flex', justifyContent: 'center', margin: '20px 0' }}>
        <div style={{ position: 'relative', width: '180px', height: '180px' }}>
          <svg width="180" height="180" style={{ transform: 'rotate(-90deg)' }}>
            {/* Background circle */}
            <circle
              cx="90"
              cy="90"
              r="75"
              fill="none"
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="12"
            />
            {/* Progress circle */}
            <circle
              cx="90"
              cy="90"
              r="75"
              fill="none"
              stroke={getScoreColor(carbonReadinessIndex.score)}
              strokeWidth="12"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              style={{
                transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1)',
                filter: `drop-shadow(0 0 8px ${getScoreColor(carbonReadinessIndex.score)})`
              }}
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
              fontWeight: 800,
              color: getScoreColor(carbonReadinessIndex.score),
              lineHeight: 1,
              letterSpacing: '-2px'
            }}>
              {carbonReadinessIndex.score.toFixed(1)}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--neutral-400)', marginTop: '4px', fontWeight: 500 }}>
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
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill"
              style={{ width: `${carbonReadinessIndex.components.netCarbonPosition.score}%` }}
            />
          </div>
          <div className="component-details" style={{ marginTop: '8px' }}>
            Weight: {(carbonReadinessIndex.components.netCarbonPosition.weight * 100).toFixed(0)}% •
            Contribution: {carbonReadinessIndex.components.netCarbonPosition.contribution.toFixed(1)} pts
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
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill"
              style={{ width: `${carbonReadinessIndex.components.socTrend.score}%` }}
            />
          </div>
          <div className="component-details" style={{ marginTop: '8px' }}>
            Weight: {(carbonReadinessIndex.components.socTrend.weight * 100).toFixed(0)}% •
            Contribution: {carbonReadinessIndex.components.socTrend.contribution.toFixed(1)} pts
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
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill"
              style={{ width: `${carbonReadinessIndex.components.managementPractices.score}%` }}
            />
          </div>
          <div className="component-details" style={{ marginTop: '8px' }}>
            Weight: {(carbonReadinessIndex.components.managementPractices.weight * 100).toFixed(0)}% •
            Contribution: {carbonReadinessIndex.components.managementPractices.contribution.toFixed(1)} pts
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

      <div className="info-footer">
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
