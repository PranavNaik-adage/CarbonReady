import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
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
    <div className="chart-container">
      <h2>📈 Historical Trends</h2>
      
      <div style={{ 
        marginBottom: '24px',
        padding: '12px 16px',
        background: 'var(--neutral-50)',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <span style={{ fontSize: '14px', color: 'var(--neutral-600)' }}>
          📊 Showing {chartData.length} data points from the last {data.days} days
        </span>
      </div>

      {/* Carbon Balance Chart */}
      <div style={{ marginBottom: '40px' }}>
        <h3 style={{ 
          fontSize: '17px', 
          marginBottom: '20px', 
          color: 'var(--neutral-700)',
          fontWeight: 600 
        }}>
          🌍 Carbon Balance Over Time
        </h3>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorSequestration" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#28a745" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#28a745" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorEmissions" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#dc3545" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#dc3545" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--neutral-300)" />
            <XAxis 
              dataKey="date" 
              style={{ fontSize: '12px' }}
              stroke="var(--neutral-600)"
            />
            <YAxis 
              style={{ fontSize: '12px' }}
              stroke="var(--neutral-600)"
              label={{ 
                value: 'kg CO₂e/year', 
                angle: -90, 
                position: 'insideLeft',
                style: { fill: 'var(--neutral-600)' }
              }}
            />
            <Tooltip 
              contentStyle={{ 
                background: 'white', 
                border: '1px solid var(--neutral-200)',
                borderRadius: '8px',
                boxShadow: 'var(--card-shadow)'
              }}
            />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
            />
            <Area
              type="monotone" 
              dataKey="sequestration" 
              stroke="#28a745" 
              fill="url(#colorSequestration)"
              name="Sequestration"
              strokeWidth={3}
            />
            <Area
              type="monotone" 
              dataKey="emissions" 
              stroke="#dc3545" 
              fill="url(#colorEmissions)"
              name="Emissions"
              strokeWidth={3}
            />
            <Line 
              type="monotone" 
              dataKey="netPosition" 
              stroke="var(--primary-green)" 
              name="Net Position"
              strokeWidth={3}
              dot={{ fill: 'var(--primary-green)', r: 4 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* CRI Trend Chart */}
      {data.trends.some(t => t.carbonReadinessIndex !== undefined) && (
        <div>
          <h3 style={{ 
            fontSize: '17px', 
            marginBottom: '20px', 
            color: 'var(--neutral-700)',
            fontWeight: 600 
          }}>
            ⭐ Carbon Readiness Index Trend
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <defs>
                <linearGradient id="colorCRI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--primary-green)" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="var(--primary-green)" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--neutral-300)" />
              <XAxis 
                dataKey="date" 
                style={{ fontSize: '12px' }}
                stroke="var(--neutral-600)"
              />
              <YAxis 
                style={{ fontSize: '12px' }}
                domain={[0, 100]}
                stroke="var(--neutral-600)"
                label={{ 
                  value: 'CRI Score', 
                  angle: -90, 
                  position: 'insideLeft',
                  style: { fill: 'var(--neutral-600)' }
                }}
              />
              <Tooltip 
                contentStyle={{ 
                  background: 'white', 
                  border: '1px solid var(--neutral-200)',
                  borderRadius: '8px',
                  boxShadow: 'var(--card-shadow)'
                }}
              />
              <Legend 
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="line"
              />
              <Area
                type="monotone" 
                dataKey="cri" 
                stroke="var(--primary-green)" 
                fill="url(#colorCRI)"
                name="CRI Score"
                strokeWidth={3}
              />
              {/* Reference lines for CRI thresholds */}
              <Line 
                type="monotone" 
                y={70} 
                stroke="#28a745" 
                strokeDasharray="5 5" 
                strokeWidth={1}
                dot={false}
              />
              <Line 
                type="monotone" 
                y={40} 
                stroke="#ffc107" 
                strokeDasharray="5 5" 
                strokeWidth={1}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
          <div style={{ 
            marginTop: '16px',
            display: 'flex',
            gap: '16px',
            fontSize: '12px',
            color: 'var(--neutral-600)',
            justifyContent: 'center'
          }}>
            <span>🟢 Excellent: &gt;70</span>
            <span>🟡 Moderate: 40-70</span>
            <span>🔴 Needs Improvement: &lt;40</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default HistoricalTrendsChart;
