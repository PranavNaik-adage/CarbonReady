import { useState } from 'react';
import type { CarbonReadinessIndex, CarbonPosition } from '../types';

interface Props {
  data: CarbonReadinessIndex;
  carbonPosition?: CarbonPosition | null;
}

function CRICard({ data, carbonPosition }: Props) {
  const [expanded, setExpanded] = useState(false);
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

  const getInterpretationMessage = () => {
    const isSink = carbonPosition?.classification === 'Net Carbon Sink';
    const socStatus = socTrend.status;
    
    if (isSink && socStatus === 'Improving') {
      return 'Your farm is acting as a Net Carbon Sink and actively improving soil carbon levels.';
    } else if (isSink && socStatus === 'Stable') {
      return 'Your farm is acting as a Net Carbon Sink and maintaining healthy soil carbon levels.';
    } else if (isSink) {
      return 'Your farm is acting as a Net Carbon Sink, sequestering more carbon than it emits.';
    } else if (socStatus === 'Improving') {
      return 'Your farm is improving soil carbon levels. Focus on reducing emissions to become carbon neutral.';
    } else if (socStatus === 'Declining') {
      return 'Your farm needs attention. Consider practices to reduce emissions and improve soil health.';
    } else {
      return 'Your farm is being monitored. Continue sustainable practices to improve your score.';
    }
  };

  const circumference = 2 * Math.PI * 75;
  const strokeDashoffset = circumference - (carbonReadinessIndex.score / 100) * circumference;

  return (
    <div className="card">
      <div className="card-header-toggle" onClick={() => setExpanded(!expanded)}>
        <h2>⭐ Farm Sustainability Score</h2>
        <span className={`card-chevron ${expanded ? 'expanded' : ''}`}>▼</span>
      </div>

      {/* Mobile Summary — key metrics when collapsed */}
      <div className={`card-summary ${expanded ? 'hidden' : ''}`}>
        <div className="card-summary-row">
          <span className="card-summary-label">CRI Score</span>
          <span className="card-summary-value" style={{ color: getScoreColor(carbonReadinessIndex.score) }}>
            {carbonReadinessIndex.score.toFixed(1)} <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--neutral-400)' }}>/ 100</span>
          </span>
        </div>
        <div className="card-summary-row">
          <span className="card-summary-label">Classification</span>
          <span className={getClassificationBadge(carbonReadinessIndex.classification)} style={{ fontSize: '11px' }}>
            {carbonReadinessIndex.classification}
          </span>
        </div>
        <div className="card-summary-row">
          <span className="card-summary-label">SOC Trend</span>
          <span className={getSOCBadge(socTrend.status)} style={{ fontSize: '11px' }}>
            {socTrend.status}
          </span>
        </div>
        <span className="card-expand-hint">Tap to see details</span>
      </div>

      {/* Full Details */}
      <div className={`card-details ${expanded ? 'expanded' : 'collapsed'}`} style={{ maxHeight: expanded ? '3000px' : undefined }}>
        <div className="card-header-divider" />

        {/* Circular Progress Indicator */}
        <div style={{ display: 'flex', justifyContent: 'center', margin: '20px 0', padding: '30px 0' }}>
          <div style={{ position: 'relative', width: '180px', height: '180px' }}>
            <svg width="200" height="200" viewBox="0 0 200 200" style={{ transform: 'rotate(-90deg)', overflow: 'visible' }}>
              <defs>
                <filter id="criGlow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
              <circle
                cx="100"
                cy="100"
                r="75"
                fill="none"
                stroke="rgba(255,255,255,0.06)"
                strokeWidth="12"
              />
              <circle
                cx="100"
                cy="100"
                r="75"
                fill="none"
                stroke={getScoreColor(carbonReadinessIndex.score)}
                strokeWidth="12"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                filter="url(#criGlow)"
                style={{
                  transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1)'
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

        <div style={{ textAlign: 'center', marginBottom: '12px' }}>
          <div style={{ fontSize: '11px', color: 'var(--neutral-400)', marginBottom: '8px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Carbon Readiness Index (CRI)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span className={getClassificationBadge(carbonReadinessIndex.classification)}>
              {carbonReadinessIndex.classification === 'Excellent' ? '🟢 Excellent' :
               carbonReadinessIndex.classification === 'Moderate' ? '🟡 Moderate' : '🔴 Needs Improvement'}
            </span>
            {/* Trend indicator - placeholder for future implementation */}
            {carbonReadinessIndex.score >= 70 && (
              <span style={{
                fontSize: '11px',
                color: 'var(--green-400)',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}>
                ↑ Improving
              </span>
            )}
          </div>
        </div>

        {/* Interpretation Message */}
        <div style={{
          background: 'var(--bg-elevated)',
          padding: '14px 16px',
          borderRadius: '10px',
          marginBottom: '24px',
          border: '1px solid var(--border-subtle)',
          fontSize: '13px',
          color: 'var(--neutral-600)',
          lineHeight: '1.6',
          textAlign: 'center'
        }}>
          <span style={{ marginRight: '6px' }}>💡</span>
          {getInterpretationMessage()}
        </div>

        <div className="component-breakdown">
          <h3>📈 Component Breakdown</h3>

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
          <h3>🌾 Soil Carbon Trend</h3>
          <div className="breakdown-item">
            <span className="breakdown-label">Status</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className={getSOCBadge(socTrend.status)}>
                {socTrend.status === 'Improving' ? '🟢 Improving' :
                 socTrend.status === 'Stable' ? '🟡 Stable' :
                 socTrend.status === 'Declining' ? '🔴 Declining' : socTrend.status}
              </span>
              {socTrend.status === 'Improving' && (
                <span style={{ fontSize: '11px', color: 'var(--green-400)', fontWeight: 600 }}>
                  ↑ Increasing trend
                </span>
              )}
              {socTrend.status === 'Declining' && (
                <span style={{ fontSize: '11px', color: 'var(--red-400)', fontWeight: 600 }}>
                  ↓ Decreasing trend
                </span>
              )}
            </div>
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
    </div>
  );
}

export default CRICard;
