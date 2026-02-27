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

  return (
    <div className="card">
      <h2>Carbon Readiness Index</h2>

      <div className="metric">
        <div className="metric-label">CRI Score</div>
        <div>
          <span className="metric-value">
            {carbonReadinessIndex.score.toFixed(1)}
          </span>
          <span className="metric-unit">/ 100</span>
          <span className={getClassificationBadge(carbonReadinessIndex.classification)}>
            {carbonReadinessIndex.classification}
          </span>
        </div>
      </div>

      <div className="component-breakdown">
        <h3>Component Breakdown</h3>
        
        <div className="component-item">
          <div className="component-header">
            <span className="component-name">Net Carbon Position</span>
            <span className="component-score">
              {carbonReadinessIndex.components.netCarbonPosition.score.toFixed(1)}
            </span>
          </div>
          <div className="component-details">
            Weight: {(carbonReadinessIndex.components.netCarbonPosition.weight * 100).toFixed(0)}% • 
            Contribution: {carbonReadinessIndex.components.netCarbonPosition.contribution.toFixed(1)} points
          </div>
        </div>

        <div className="component-item">
          <div className="component-header">
            <span className="component-name">Soil Organic Carbon Trend</span>
            <span className="component-score">
              {carbonReadinessIndex.components.socTrend.score.toFixed(1)}
            </span>
          </div>
          <div className="component-details">
            Weight: {(carbonReadinessIndex.components.socTrend.weight * 100).toFixed(0)}% • 
            Contribution: {carbonReadinessIndex.components.socTrend.contribution.toFixed(1)} points
          </div>
        </div>

        <div className="component-item">
          <div className="component-header">
            <span className="component-name">Management Practices</span>
            <span className="component-score">
              {carbonReadinessIndex.components.managementPractices.score.toFixed(1)}
            </span>
          </div>
          <div className="component-details">
            Weight: {(carbonReadinessIndex.components.managementPractices.weight * 100).toFixed(0)}% • 
            Contribution: {carbonReadinessIndex.components.managementPractices.contribution.toFixed(1)} points
          </div>
        </div>
      </div>

      <div className="breakdown" style={{ marginTop: '20px' }}>
        <h3>Soil Organic Carbon Trend</h3>
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

      <div style={{ marginTop: '15px', fontSize: '12px', color: '#999' }}>
        Scoring Logic: {carbonReadinessIndex.scoringLogicVersion} • 
        Calculated: {new Date(carbonReadinessIndex.calculatedAt).toLocaleString()}
      </div>
    </div>
  );
}

export default CRICard;
