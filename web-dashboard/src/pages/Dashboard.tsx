import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api';
import type {
  CarbonPosition,
  CarbonReadinessIndex,
  SensorData,
  HistoricalTrends
} from '../types';
import CarbonPositionCard from '../components/CarbonPositionCard';
import CRICard from '../components/CRICard';
import SensorDataCard from '../components/SensorDataCard';
import HistoricalTrendsChart from '../components/HistoricalTrendsChart';

function Dashboard() {
  const { farmId } = useParams<{ farmId: string }>();
  const [carbonPosition, setCarbonPosition] = useState<CarbonPosition | null>(null);
  const [cri, setCRI] = useState<CarbonReadinessIndex | null>(null);
  const [sensorData, setSensorData] = useState<SensorData | null>(null);
  const [historicalTrends, setHistoricalTrends] = useState<HistoricalTrends | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!farmId) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [positionData, criData, sensorDataResult, trendsData] = await Promise.all([
          api.getCarbonPosition(farmId),
          api.getCarbonReadinessIndex(farmId),
          api.getLatestSensorData(farmId),
          api.getHistoricalTrends(farmId, 365)
        ]);

        setCarbonPosition(positionData);
        setCRI(criData);
        setSensorData(sensorDataResult);
        setHistoricalTrends(trendsData);
      } catch (err) {
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
        <div className="dashboard-grid">
          {carbonPosition && <CarbonPositionCard data={carbonPosition} />}
          {cri && <CRICard data={cri} />}
          {sensorData && <SensorDataCard data={sensorData} />}
        </div>

        {historicalTrends && (
          <HistoricalTrendsChart data={historicalTrends} />
        )}
      </div>
    </>
  );
}

export default Dashboard;
