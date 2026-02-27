import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
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
      <div className="app">
        <header className="header">
          <div className="container">
            <h1>CarbonReady Dashboard</h1>
            <p>Carbon Intelligence for Smallholder Farms</p>
            <nav className="nav">
              <Link to={`/dashboard/${farmId}`} className="active">Dashboard</Link>
              <Link to="/admin">Admin Panel</Link>
            </nav>
          </div>
        </header>
        <div className="container">
          <div className="loading">Loading dashboard data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <header className="header">
          <div className="container">
            <h1>CarbonReady Dashboard</h1>
            <p>Carbon Intelligence for Smallholder Farms</p>
            <nav className="nav">
              <Link to={`/dashboard/${farmId}`} className="active">Dashboard</Link>
              <Link to="/admin">Admin Panel</Link>
            </nav>
          </div>
        </header>
        <div className="container">
          <div className="error">
            <strong>Error:</strong> {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <h1>CarbonReady Dashboard</h1>
          <p>Farm: {farmId}</p>
          <nav className="nav">
            <Link to={`/dashboard/${farmId}`} className="active">Dashboard</Link>
            <Link to="/admin">Admin Panel</Link>
          </nav>
        </div>
      </header>

      <div className="container">
        <div className="dashboard-grid">
          {carbonPosition && <CarbonPositionCard data={carbonPosition} />}
          {cri && <CRICard data={cri} />}
          {sensorData && <SensorDataCard data={sensorData} />}
        </div>

        {historicalTrends && (
          <div style={{ marginTop: '20px' }}>
            <HistoricalTrendsChart data={historicalTrends} />
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
