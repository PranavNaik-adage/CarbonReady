import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import type { HistoricalTrends } from '../types';

interface Props {
  data: HistoricalTrends;
}

function HistoricalTrendsChart({ data }: Props) {
  // Format data for chart - show last 12 months
  const chartData = data.trends
    .slice(-12)
    .map(trend => ({
      date: new Date(trend.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
      netPosition: trend.netCarbonPosition,
      sequestration: trend.annualSequestration,
      emissions: trend.totalEmissions,
      cri: trend.carbonReadinessIndex
    }));

  return (
    <div className="card">
      <h2>Historical Trends (Last 12 Months)</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <p style={{ fontSize: '14px', color: '#666' }}>
          Showing {chartData.length} data points from the last {data.days} days
        </p>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              style={{ fontSize: '12px' }}
              label={{ value: 'kg CO₂e/year', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="netPosition" 
              stroke="#2c5f2d" 
              name="Net Carbon Position"
              strokeWidth={2}
            />
            <Line 
              type="monotone" 
              dataKey="sequestration" 
              stroke="#28a745" 
              name="Sequestration"
              strokeWidth={2}
            />
            <Line 
              type="monotone" 
              dataKey="emissions" 
              stroke="#dc3545" 
              name="Emissions"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {data.trends.some(t => t.carbonReadinessIndex !== undefined) && (
        <div className="chart-container" style={{ marginTop: '30px' }}>
          <h3>Carbon Readiness Index Trend</h3>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                style={{ fontSize: '12px' }}
              />
              <YAxis 
                style={{ fontSize: '12px' }}
                domain={[0, 100]}
                label={{ value: 'CRI Score', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="cri" 
                stroke="#2c5f2d" 
                name="CRI Score"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default HistoricalTrendsChart;
