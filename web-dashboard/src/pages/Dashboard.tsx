import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api';
import type {
  CarbonPosition,
  CarbonReadinessIndex,
  SensorData,
  HistoricalTrends,
  FarmMetadata
} from '../types';
import CarbonPositionCard from '../components/CarbonPositionCard';
import CRICard from '../components/CRICard';
import SensorDataCard from '../components/SensorDataCard';
import HistoricalTrendsChart from '../components/HistoricalTrendsChart';
import CarbonOpportunityCard from '../components/CarbonOpportunityCard';
import ClimateImpactCard from '../components/ClimateImpactCard';

function Dashboard() {
  const { farmId } = useParams<{ farmId: string }>();
  const [carbonPosition, setCarbonPosition] = useState<CarbonPosition | null>(null);
  const [cri, setCRI] = useState<CarbonReadinessIndex | null>(null);
  const [sensorData, setSensorData] = useState<SensorData | null>(null);
  const [historicalTrends, setHistoricalTrends] = useState<HistoricalTrends | null>(null);
  const [farmMetadata, setFarmMetadata] = useState<FarmMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!farmId) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Fetch data sequentially in batches to avoid throttling
        // Batch 1: Critical data
        const [positionData, criData] = await Promise.all([
          api.getCarbonPosition(farmId),
          api.getCarbonReadinessIndex(farmId)
        ]);

        // Small delay to avoid throttling
        await new Promise(resolve => setTimeout(resolve, 100));

        // Batch 2: Supporting data
        const [sensorDataResult, trendsData, metadataResult] = await Promise.all([
          api.getLatestSensorData(farmId),
          api.getHistoricalTrends(farmId, 365),
          api.getFarmMetadata(farmId)
        ]);

        console.log('Carbon Position Data:', positionData);
        console.log('CRI Data:', criData);
        console.log('Sensor Data:', sensorDataResult);
        console.log('Historical Trends:', trendsData);
        console.log('Farm Metadata:', metadataResult);

        setCarbonPosition(positionData);
        setCRI(criData);
        setSensorData(sensorDataResult);
        setHistoricalTrends(trendsData);
        setFarmMetadata(metadataResult);
      } catch (err) {
        console.error('Dashboard fetch error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [farmId]);

  if (loading) {
    return (
      <>
        <div className="page-header">
          <h2>📊 Dashboard</h2>
          <span className="page-header-sub">Loading...</span>
        </div>
        <div className="container">
          <div className="loading">
            <div className="loading-spinner" />
            <div className="loading-text">Loading dashboard data...</div>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <div className="page-header">
          <h2>📊 Dashboard</h2>
          <span className="page-header-sub">Farm: {farmId}</span>
        </div>
        <div className="container">
          <div className="error">
            <strong>Error:</strong> {error}
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="page-header">
        <h2>📊 Dashboard</h2>
        <span className="page-header-sub">Farm: {farmId}</span>
      </div>

      <div className="container">
        {/* Farm Summary Header */}
        <div className="farm-summary-header">
          <div className="farm-summary-main">
            <div className="farm-summary-item">
              <span className="farm-summary-icon">🏡</span>
              <div>
                <div className="farm-summary-label">Farm Name</div>
                <div className="farm-summary-value">{farmMetadata?.farmName || farmId}</div>
              </div>
            </div>
            <div className="farm-summary-item">
              <span className="farm-summary-icon">📍</span>
              <div>
                <div className="farm-summary-label">Location</div>
                <div className="farm-summary-value">{farmMetadata?.location || 'Not specified'}</div>
              </div>
            </div>
            <div className="farm-summary-item">
              <span className="farm-summary-icon">🌴</span>
              <div>
                <div className="farm-summary-label">Crop Type</div>
                <div className="farm-summary-value">
                  {farmMetadata?.cropType ? 
                    farmMetadata.cropType.charAt(0).toUpperCase() + farmMetadata.cropType.slice(1) : 
                    'Not specified'}
                </div>
              </div>
            </div>
            <div className="farm-summary-item">
              <span className="farm-summary-icon">📏</span>
              <div>
                <div className="farm-summary-label">Farm Size</div>
                <div className="farm-summary-value">
                  {farmMetadata?.farmSizeHectares ? 
                    `${Number(farmMetadata.farmSizeHectares).toFixed(1)} ha` : 
                    'Not specified'}
                </div>
              </div>
            </div>
          </div>
          <div className="farm-summary-metrics">
            <div className="farm-summary-metric">
              <div className="farm-summary-metric-label">Sustainability Score</div>
              <div className="farm-summary-metric-value" style={{ 
                color: cri && cri.carbonReadinessIndex.score >= 70 ? 'var(--green-400)' : 
                       cri && cri.carbonReadinessIndex.score >= 40 ? 'var(--amber-400)' : 'var(--red-400)' 
              }}>
                {cri ? cri.carbonReadinessIndex.score.toFixed(0) : '--'}/100
                {cri && (
                  <span style={{ 
                    fontSize: '11px', 
                    marginLeft: '6px',
                    color: cri.carbonReadinessIndex.score >= 70 ? 'var(--green-400)' : 
                           cri.carbonReadinessIndex.score >= 40 ? 'var(--amber-400)' : 'var(--red-400)'
                  }}>
                    {cri.carbonReadinessIndex.score >= 70 ? '🟢 Excellent' : 
                     cri.carbonReadinessIndex.score >= 40 ? '🟡 Moderate' : '🔴 Needs Improvement'}
                  </span>
                )}
              </div>
            </div>
            <div className="farm-summary-metric">
              <div className="farm-summary-metric-label">Net Carbon Position</div>
              <div className="farm-summary-metric-value" style={{ 
                color: carbonPosition?.classification === 'Net Carbon Sink' ? 'var(--green-400)' : 'var(--red-400)' 
              }}>
                {carbonPosition ? `${carbonPosition.classification === 'Net Carbon Sink' ? '+' : ''}${carbonPosition.netCarbonPosition.toFixed(0)}` : '--'} kg CO₂e/yr
              </div>
            </div>
          </div>
        </div>

        {/* System Status */}
        {sensorData && (
          <div style={{
            background: 'var(--bg-elevated)',
            borderRadius: '12px',
            padding: '14px 20px',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            border: '1px solid var(--border-subtle)',
            flexWrap: 'wrap',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div className="live-dot" style={{ width: '8px', height: '8px' }} />
                <span style={{ fontSize: '13px', color: 'var(--green-400)', fontWeight: 600 }}>
                  System Online
                </span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--neutral-500)' }}>
                Last Update: {new Date(sensorData.timestamp).toLocaleString()}
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', color: 'var(--neutral-400)' }}>Device:</span>
              <span className="badge excellent" style={{ fontSize: '11px' }}>
                🟢 Active
              </span>
            </div>
          </div>
        )}

        {/* Carbon Intelligence Section */}
        <div className="dashboard-section">
          <div className="dashboard-section-header">
            <h3>🌍 Carbon Intelligence</h3>
            <p>Understanding your farm's carbon footprint and sustainability performance</p>
          </div>
          <div className="dashboard-grid">
            {carbonPosition && <CarbonPositionCard data={carbonPosition} />}
            {cri && <CRICard data={cri} carbonPosition={carbonPosition} />}
            {carbonPosition && cri && <CarbonOpportunityCard carbonPosition={carbonPosition} cri={cri} />}
            {carbonPosition && <ClimateImpactCard carbonPosition={carbonPosition} />}
          </div>
        </div>

        {/* Environmental Conditions Section */}
        <div className="dashboard-section">
          <div className="dashboard-section-header">
            <h3>🌤️ Environmental Conditions</h3>
            <p>Real-time monitoring of soil and weather conditions</p>
          </div>
          <div className="dashboard-grid">
            {sensorData && <SensorDataCard data={sensorData} />}
          </div>
        </div>

        {historicalTrends && (
          <HistoricalTrendsChart data={historicalTrends} />
        )}
      </div>
    </>
  );
}

export default Dashboard;
