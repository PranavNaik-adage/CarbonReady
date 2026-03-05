import { useEffect, useState } from 'react';
import { api } from '../api';
import type {
    CarbonPosition,
    CarbonReadinessIndex,
    SensorData
} from '../types';

// Helper to generate insights dynamically from data
function generateInsights(
    carbon: CarbonPosition | null,
    cri: CarbonReadinessIndex | null,
    sensor: SensorData | null
): { icon: string; title: string; description: string; type: 'success' | 'warning' | 'info' }[] {
    const insights: { icon: string; title: string; description: string; type: 'success' | 'warning' | 'info' }[] = [];

    if (carbon) {
        if (carbon.classification === 'Net Carbon Sink') {
            insights.push({
                icon: '🎉',
                title: 'Carbon Positive Farm',
                description: `Your farm sequesters ${carbon.annualSequestration?.toFixed(0) || 0} kg CO₂e/yr more than it emits. Keep up the great work!`,
                type: 'success'
            });
        } else if (carbon.emissions?.totalEmissions) {
            insights.push({
                icon: '⚡',
                title: 'Reduce Emissions',
                description: `Your farm emits ${carbon.emissions.totalEmissions.toFixed(0)} kg CO₂e/yr. Consider cover cropping and reduced tillage.`,
                type: 'warning'
            });
        }

        if (carbon.emissions?.fertilizerEmissions && carbon.emissions?.irrigationEmissions && 
            carbon.emissions.fertilizerEmissions > carbon.emissions.irrigationEmissions * 2) {
            insights.push({
                icon: '🧪',
                title: 'Optimize Fertilizer Use',
                description: 'Fertilizer is your largest emission source. Consider slow-release fertilizers or compost alternatives.',
                type: 'warning'
            });
        }
    }

    if (sensor) {
        if (sensor.readings?.soilMoisture !== undefined) {
            if (sensor.readings.soilMoisture < 30) {
                insights.push({
                    icon: '💧',
                    title: 'Low Soil Moisture',
                    description: `Soil moisture is at ${sensor.readings.soilMoisture.toFixed(1)}%. Consider irrigation or mulching to retain water.`,
                    type: 'warning'
                });
            } else if (sensor.readings.soilMoisture > 40 && sensor.readings.soilMoisture < 65) {
                insights.push({
                    icon: '💧',
                    title: 'Healthy Moisture Level',
                    description: `Soil moisture is at ${sensor.readings.soilMoisture.toFixed(1)}% — ideal for most crops. Well managed!`,
                    type: 'success'
                });
            }
        }

        if (sensor.readings?.soilTemperature !== undefined && sensor.readings.soilTemperature > 30) {
            insights.push({
                icon: '🌡️',
                title: 'High Soil Temperature',
                description: 'Soil temperature is above 30°C. Apply mulch to reduce heat stress on roots.',
                type: 'warning'
            });
        }
    }

    if (cri) {
        if (cri.socTrend.status === 'Improving') {
            insights.push({
                icon: '📈',
                title: 'Soil Health Improving',
                description: 'Your soil organic carbon is trending upward. Your management practices are working.',
                type: 'success'
            });
        } else if (cri.socTrend.status === 'Declining') {
            insights.push({
                icon: '📉',
                title: 'Soil Health Declining',
                description: 'Soil organic carbon is decreasing. Consider adding organic matter and reducing tillage.',
                type: 'warning'
            });
        }
    }

    if (insights.length === 0) {
        insights.push({
            icon: 'ℹ️',
            title: 'Monitoring Active',
            description: 'Your farm is being monitored. Insights will appear as more data is collected.',
            type: 'info'
        });
    }

    return insights;
}

function FarmerDashboard() {
    const farmId = 'farm-001';
    const [carbonPosition, setCarbonPosition] = useState<CarbonPosition | null>(null);
    const [cri, setCRI] = useState<CarbonReadinessIndex | null>(null);
    const [sensorData, setSensorData] = useState<SensorData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const [positionData, criData, sensorResult] = await Promise.all([
                    api.getCarbonPosition(farmId),
                    api.getCarbonReadinessIndex(farmId),
                    api.getLatestSensorData(farmId)
                ]);
                setCarbonPosition(positionData);
                setCRI(criData);
                setSensorData(sensorResult);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load farm data');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return (
            <>
                <div className="page-header">
                    <h2>🌾 Farmer Dashboard</h2>
                    <span className="page-header-sub">Loading...</span>
                </div>
                <div className="container">
                    <div className="loading">
                        <div className="loading-spinner" />
                        <div className="loading-text">Loading your farm data...</div>
                    </div>
                </div>
            </>
        );
    }

    if (error) {
        return (
            <>
                <div className="page-header">
                    <h2>🌾 Farmer Dashboard</h2>
                </div>
                <div className="container">
                    <div className="error">
                        <strong>Error:</strong> {error}
                    </div>
                </div>
            </>
        );
    }

    const sustainabilityScore = cri ? cri.carbonReadinessIndex.score : 0;
    const insights = generateInsights(carbonPosition, cri, sensorData);

    // Carbon opportunity
    const currentSequestration = carbonPosition?.annualSequestration || 0;
    const potentialExtra = currentSequestration * 0.25; // 25% improvement potential estimate
    const potentialValue = potentialExtra * 0.05; // ~$0.05/kg CO2e market estimate

    return (
        <>
            <div className="page-header">
                <h2>🌾 Farmer Dashboard</h2>
                <span className="page-header-sub">Your farm at a glance</span>
            </div>

            <div className="container">
                {/* === Row 1: Sustainability Score + Soil Carbon Status === */}
                <div className="farmer-grid-2">

                    {/* Farm Sustainability Score */}
                    <div className="card farmer-card-hero">
                        <h2>🏆 Farm Sustainability Score</h2>
                        <div className="farmer-score-container">
                            <div className="farmer-score-ring">
                                <svg width="200" height="200" viewBox="0 0 200 200" style={{ transform: 'rotate(-90deg)', overflow: 'visible' }}>
                                    <defs>
                                        <filter id="farmerGlow" x="-50%" y="-50%" width="200%" height="200%">
                                            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                                            <feMerge>
                                                <feMergeNode in="coloredBlur"/>
                                                <feMergeNode in="SourceGraphic"/>
                                            </feMerge>
                                        </filter>
                                    </defs>
                                    <circle cx="100" cy="100" r="68" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
                                    <circle
                                        cx="100" cy="100" r="68" fill="none"
                                        stroke={sustainabilityScore >= 70 ? 'var(--green-400)' : sustainabilityScore >= 40 ? 'var(--amber-400)' : 'var(--red-400)'}
                                        strokeWidth="10"
                                        strokeDasharray={2 * Math.PI * 68}
                                        strokeDashoffset={(2 * Math.PI * 68) - (sustainabilityScore / 100) * (2 * Math.PI * 68)}
                                        strokeLinecap="round"
                                        filter="url(#farmerGlow)"
                                        style={{
                                            transition: 'stroke-dashoffset 1.5s cubic-bezier(0.16, 1, 0.3, 1)'
                                        }}
                                    />
                                </svg>
                                <div className="farmer-score-text">
                                    <div className="farmer-score-number" style={{
                                        color: sustainabilityScore >= 70 ? 'var(--green-400)' : sustainabilityScore >= 40 ? 'var(--amber-400)' : 'var(--red-400)'
                                    }}>
                                        {sustainabilityScore.toFixed(0)}
                                    </div>
                                    <div className="farmer-score-label">out of 100</div>
                                </div>
                            </div>
                            <div className="farmer-score-badge">
                                <span className={`badge ${sustainabilityScore >= 70 ? 'excellent' : sustainabilityScore >= 40 ? 'moderate' : 'needs-improvement'}`}>
                                    {sustainabilityScore >= 70 ? 'Excellent' : sustainabilityScore >= 40 ? 'Moderate' : 'Needs Improvement'}
                                </span>
                            </div>
                            <div className="farmer-score-hint">
                                Based on carbon balance, soil health, and farming practices
                            </div>
                        </div>
                    </div>

                    {/* Soil Carbon Status */}
                    <div className="card">
                        <h2>🌱 Soil Carbon Status</h2>
                        {carbonPosition && (
                            <>
                                <div className="farmer-stat-row">
                                    <div className="farmer-stat">
                                        <div className="farmer-stat-label">Net Carbon Balance</div>
                                        <div className="farmer-stat-value" style={{ color: carbonPosition.classification === 'Net Carbon Sink' ? 'var(--green-400)' : 'var(--red-400)' }}>
                                            {carbonPosition.classification === 'Net Carbon Sink' ? '+' : ''}{carbonPosition.netCarbonPosition.toFixed(0)}
                                            <span className="farmer-stat-unit">kg CO₂e/yr</span>
                                        </div>
                                    </div>
                                    <div className="farmer-stat">
                                        <div className="farmer-stat-label">Classification</div>
                                        <span className={carbonPosition.classification === 'Net Carbon Sink' ? 'badge sink' : 'badge source'}>
                                            {carbonPosition.classification === 'Net Carbon Sink' ? '🟢 Carbon Sink' : '🔴 Carbon Source'}
                                        </span>
                                    </div>
                                </div>

                                <div className="farmer-carbon-bar">
                                    <div className="farmer-carbon-bar-labels">
                                        <span style={{ color: 'var(--green-400)' }}>🌱 Sequestration</span>
                                        <span style={{ color: 'var(--red-400)' }}>💨 Emissions</span>
                                    </div>
                                    <div className="farmer-carbon-bar-track">
                                        <div
                                            className="farmer-carbon-bar-fill-green"
                                            style={{
                                                width: `${(carbonPosition.annualSequestration / (carbonPosition.annualSequestration + (carbonPosition.emissions?.totalEmissions || 1))) * 100}%`
                                            }}
                                        />
                                    </div>
                                    <div className="farmer-carbon-bar-values">
                                        <span style={{ color: 'var(--green-400)' }}>+{carbonPosition.annualSequestration.toFixed(0)}</span>
                                        <span style={{ color: 'var(--red-400)' }}>-{(carbonPosition.emissions?.totalEmissions || 0).toFixed(0)}</span>
                                    </div>
                                </div>

                                <div className="farmer-stat-row" style={{ marginTop: '20px' }}>
                                    <div className="farmer-stat">
                                        <div className="farmer-stat-label">Carbon Stock</div>
                                        <div className="farmer-stat-value">
                                            {carbonPosition.carbonStock.toFixed(0)}
                                            <span className="farmer-stat-unit">kg C</span>
                                        </div>
                                    </div>
                                    <div className="farmer-stat">
                                        <div className="farmer-stat-label">SOC Trend</div>
                                        <span className={`badge ${cri?.socTrend.status === 'Improving' ? 'improving' : cri?.socTrend.status === 'Stable' ? 'stable' : cri?.socTrend.status === 'Declining' ? 'declining' : 'moderate'}`}>
                                            {cri?.socTrend.status || 'Unknown'}
                                        </span>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                {/* === Row 2: Farm Conditions === */}
                <div className="card" style={{ marginTop: '24px' }}>
                    <h2>🌤️ Farm Conditions</h2>
                    {sensorData && (
                        <>
                            <div className="farmer-conditions-grid">
                                <div className="farmer-condition-item">
                                    <div className="farmer-condition-icon">💧</div>
                                    <div className="farmer-condition-data">
                                        <div className="farmer-condition-label">Soil Moisture</div>
                                        <div className="farmer-condition-value" style={{
                                            color: sensorData.readings.soilMoisture < 30 ? 'var(--red-400)' :
                                                sensorData.readings.soilMoisture > 70 ? 'var(--blue-400)' : 'var(--green-400)'
                                        }}>
                                            {sensorData.readings.soilMoisture.toFixed(1)}%
                                        </div>
                                        <div className="progress-bar-track" style={{ marginTop: '6px' }}>
                                            <div className="progress-bar-fill" style={{
                                                width: `${sensorData.readings.soilMoisture}%`,
                                                background: sensorData.readings.soilMoisture < 30 ? 'var(--red-400)' :
                                                    sensorData.readings.soilMoisture > 70 ? 'var(--blue-400)' : 'var(--green-400)'
                                            }} />
                                        </div>
                                    </div>
                                </div>

                                <div className="farmer-condition-item">
                                    <div className="farmer-condition-icon">🌡️</div>
                                    <div className="farmer-condition-data">
                                        <div className="farmer-condition-label">Soil Temperature</div>
                                        <div className="farmer-condition-value">
                                            {sensorData.readings.soilTemperature.toFixed(1)}°C
                                        </div>
                                        <div className="farmer-condition-hint">Optimal: 20–25°C</div>
                                    </div>
                                </div>

                                <div className="farmer-condition-item">
                                    <div className="farmer-condition-icon">🌤️</div>
                                    <div className="farmer-condition-data">
                                        <div className="farmer-condition-label">Air Temperature</div>
                                        <div className="farmer-condition-value">
                                            {sensorData.readings.airTemperature.toFixed(1)}°C
                                        </div>
                                        <div className="farmer-condition-hint">Current</div>
                                    </div>
                                </div>

                                <div className="farmer-condition-item">
                                    <div className="farmer-condition-icon">💨</div>
                                    <div className="farmer-condition-data">
                                        <div className="farmer-condition-label">Humidity</div>
                                        <div className="farmer-condition-value" style={{ color: 'var(--blue-400)' }}>
                                            {sensorData.readings.humidity.toFixed(1)}%
                                        </div>
                                        <div className="progress-bar-track" style={{ marginTop: '6px' }}>
                                            <div className="progress-bar-fill" style={{
                                                width: `${sensorData.readings.humidity}%`,
                                                background: 'var(--blue-400)',
                                                boxShadow: '0 0 8px rgba(96, 165, 250, 0.3)'
                                            }} />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="live-status" style={{ marginTop: '16px' }}>
                                <div className="live-dot" />
                                <span className="live-text">Sensors Active • Last reading: {new Date(sensorData.timestamp).toLocaleString()}</span>
                            </div>
                        </>
                    )}
                </div>

                {/* === Row 3: Insights + Carbon Opportunity === */}
                <div className="farmer-grid-2" style={{ marginTop: '24px' }}>

                    {/* Farm Insights */}
                    <div className="card">
                        <h2>💡 Farm Insights & Recommendations</h2>
                        <div className="farmer-insights-list">
                            {insights.map((insight, i) => (
                                <div key={i} className={`farmer-insight farmer-insight-${insight.type}`}>
                                    <div className="farmer-insight-icon">{insight.icon}</div>
                                    <div className="farmer-insight-content">
                                        <div className="farmer-insight-title">{insight.title}</div>
                                        <div className="farmer-insight-desc">{insight.description}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Carbon Opportunity */}
                    <div className="card">
                        <h2>🚀 Carbon Opportunity</h2>
                        <div className="farmer-opportunity">
                            <div className="farmer-opportunity-header">
                                <div className="farmer-opportunity-title">Estimated Annual Potential</div>
                                <div className="farmer-opportunity-subtitle">With improved practices</div>
                            </div>

                            <div className="farmer-stat-row" style={{ marginTop: '20px' }}>
                                <div className="farmer-stat">
                                    <div className="farmer-stat-label">Current Sequestration</div>
                                    <div className="farmer-stat-value" style={{ color: 'var(--green-400)' }}>
                                        {currentSequestration.toFixed(0)}
                                        <span className="farmer-stat-unit">kg CO₂e/yr</span>
                                    </div>
                                </div>
                                <div className="farmer-stat">
                                    <div className="farmer-stat-label">Additional Potential</div>
                                    <div className="farmer-stat-value" style={{ color: 'var(--teal-400)' }}>
                                        +{potentialExtra.toFixed(0)}
                                        <span className="farmer-stat-unit">kg CO₂e/yr</span>
                                    </div>
                                </div>
                            </div>

                            <div className="farmer-opportunity-value-box">
                                <div className="farmer-opportunity-value-label">Estimated Carbon Credit Value</div>
                                <div className="farmer-opportunity-value-amount">
                                    ${potentialValue.toFixed(2)}
                                    <span className="farmer-stat-unit"> / year</span>
                                </div>
                            </div>

                            <div className="farmer-opportunity-actions">
                                <div className="farmer-opportunity-action">
                                    <span>🌿</span> Add cover crops to bare fields
                                </div>
                                <div className="farmer-opportunity-action">
                                    <span>🚜</span> Reduce tillage to minimum
                                </div>
                                <div className="farmer-opportunity-action">
                                    <span>♻️</span> Apply compost instead of synthetic fertilizers
                                </div>
                                <div className="farmer-opportunity-action">
                                    <span>🌳</span> Plant agroforestry border trees
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}

export default FarmerDashboard;
