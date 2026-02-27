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

const darkTooltipStyle = {
  background: 'rgba(22, 24, 34, 0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '10px',
  boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  color: '#e4e4e7',
  fontSize: '13px'
};

function HistoricalTrendsChart({ data }: Props) {
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

      <div className="info-footer" style={{ marginTop: 0, marginBottom: '24px' }}>
        <span>📊</span>
        <span>Showing {chartData.length} data points from the last {data.days} days</span>
      </div>

      {/* Carbon Balance Chart */}
      <div style={{ marginBottom: '48px' }}>
        <h3 style={{
          fontSize: '14px',
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
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorEmissions" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="date"
              style={{ fontSize: '11px' }}
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.45)' }}
            />
            <YAxis
              style={{ fontSize: '11px' }}
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.45)' }}
              label={{
                value: 'kg CO₂e/year',
                angle: -90,
                position: 'insideLeft',
                style: { fill: 'rgba(255,255,255,0.35)', fontSize: '11px' }
              }}
            />
            <Tooltip contentStyle={darkTooltipStyle} />
            <Legend
              wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }}
              iconType="line"
            />
            <Area
              type="monotone"
              dataKey="sequestration"
              stroke="#22c55e"
              fill="url(#colorSequestration)"
              name="Sequestration"
              strokeWidth={2.5}
            />
            <Area
              type="monotone"
              dataKey="emissions"
              stroke="#ef4444"
              fill="url(#colorEmissions)"
              name="Emissions"
              strokeWidth={2.5}
            />
            <Line
              type="monotone"
              dataKey="netPosition"
              stroke="#2dd4bf"
              name="Net Position"
              strokeWidth={2.5}
              dot={{ fill: '#2dd4bf', r: 3, strokeWidth: 0 }}
              activeDot={{ r: 5, fill: '#2dd4bf', stroke: '#0f1117', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* CRI Trend Chart */}
      {data.trends.some(t => t.carbonReadinessIndex !== undefined) && (
        <div>
          <h3 style={{
            fontSize: '14px',
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
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis
                dataKey="date"
                style={{ fontSize: '11px' }}
                stroke="rgba(255,255,255,0.3)"
                tick={{ fill: 'rgba(255,255,255,0.45)' }}
              />
              <YAxis
                style={{ fontSize: '11px' }}
                domain={[0, 100]}
                stroke="rgba(255,255,255,0.3)"
                tick={{ fill: 'rgba(255,255,255,0.45)' }}
                label={{
                  value: 'CRI Score',
                  angle: -90,
                  position: 'insideLeft',
                  style: { fill: 'rgba(255,255,255,0.35)', fontSize: '11px' }
                }}
              />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Legend
                wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }}
                iconType="line"
              />
              <Area
                type="monotone"
                dataKey="cri"
                stroke="#22c55e"
                fill="url(#colorCRI)"
                name="CRI Score"
                strokeWidth={2.5}
              />
              {/* Reference lines for CRI thresholds */}
              <Line
                type="monotone"
                y={70}
                stroke="rgba(34,197,94,0.3)"
                strokeDasharray="5 5"
                strokeWidth={1}
                dot={false}
              />
              <Line
                type="monotone"
                y={40}
                stroke="rgba(251,191,36,0.3)"
                strokeDasharray="5 5"
                strokeWidth={1}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
          <div style={{
            marginTop: '16px',
            display: 'flex',
            gap: '20px',
            fontSize: '11px',
            color: 'var(--neutral-400)',
            justifyContent: 'center',
            fontWeight: 500
          }}>
            <span>🟢 Excellent: &gt;70</span>
            <span>🟡 Moderate: 40–70</span>
            <span>🔴 Needs Improvement: &lt;40</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default HistoricalTrendsChart;
