import type {
  CarbonPosition,
  CarbonReadinessIndex,
  SensorData,
  HistoricalTrends,
  CRIWeights,
  ApiError
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true';

class ApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    // Use mock data if enabled
    if (USE_MOCK_DATA) {
      return this.getMockData<T>(endpoint);
    }

    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        const error = data as ApiError;
        throw new Error(error.error.message || 'An error occurred');
      }

      return data as T;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  }

  private async getMockData<T>(endpoint: string, options?: RequestInit): Promise<T> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 300));

    if (endpoint.includes('/carbon-position')) {
      const calculatedAt = new Date(Date.now() - 3600000).toISOString();
      const isStale = Date.now() - new Date(calculatedAt).getTime() > 24 * 60 * 60 * 1000;
      
      return {
        farmId: 'farm-001',
        netCarbonPosition: 1250.75,
        classification: 'Net Carbon Sink',
        annualSequestration: 2100.50,
        emissions: {
          fertilizerEmissions: 549.25,
          irrigationEmissions: 300.50,
          totalEmissions: 849.75,
          unit: 'kg CO2e/year'
        },
        carbonStock: 15420.30,
        co2EquivalentStock: 56525.50,
        calculatedAt,
        isStale,
        unit: 'kg CO2e/year'
      } as T;
    }

    if (endpoint.includes('/carbon-readiness-index')) {
      return {
        farmId: 'farm-001',
        carbonReadinessIndex: {
          score: 72.5,
          classification: 'Excellent',
          components: {
            netCarbonPosition: {
              score: 85,
              weight: 0.5,
              contribution: 42.5
            },
            socTrend: {
              score: 60,
              weight: 0.3,
              contribution: 18.0
            },
            managementPractices: {
              score: 60,
              weight: 0.2,
              contribution: 12.0
            }
          },
          scoringLogicVersion: 'v1.0.0',
          calculatedAt: new Date(Date.now() - 3600000).toISOString()
        },
        socTrend: {
          status: 'Improving',
          score: 0.15,
          biomassReturn: 12.5,
          managementScore: 0.75,
          dataSpanDays: 120
        },
        netCarbonPosition: 1250.75
      } as T;
    }

    if (endpoint.includes('/sensor-data/latest')) {
      return {
        farmId: 'farm-001',
        deviceId: 'esp32-001',
        timestamp: new Date(Date.now() - 1800000).toISOString(),
        readings: {
          soilMoisture: 45.2,
          soilTemperature: 24.5,
          airTemperature: 28.3,
          humidity: 72.8
        },
        validationStatus: 'valid'
      } as T;
    }

    if (endpoint.includes('/historical-trends')) {
      const trends = [];
      const now = Date.now();
      for (let i = 11; i >= 0; i--) {
        const date = new Date(now - i * 30 * 24 * 60 * 60 * 1000);
        const baseSequestration = 1800;
        const baseEmissions = 700;
        const sequestration = baseSequestration + Math.random() * 600;
        const emissions = baseEmissions + Math.random() * 300;
        
        trends.push({
          date: date.toISOString().split('T')[0],
          netCarbonPosition: sequestration - emissions,
          annualSequestration: sequestration,
          totalEmissions: emissions,
          carbonReadinessIndex: 60 + Math.random() * 20,
          socTrend: i < 4 ? 'Improving' : i < 8 ? 'Stable' : 'Improving'
        });
      }
      return {
        farmId: 'farm-001',
        days: 365,
        dataPoints: trends.length,
        trends
      } as T;
    }

    if (endpoint.includes('/admin/cri-weights')) {
      if (options?.method === 'PUT') {
        const body = JSON.parse(options.body as string);
        return {
          configId: 'cri-weights-default',
          version: 2,
          weights: body,
          updatedAt: new Date().toISOString(),
          updatedBy: 'admin@carbonready.com'
        } as T;
      }
      return {
        configId: 'cri-weights-default',
        version: 1,
        weights: {
          netCarbonPosition: 0.5,
          socTrend: 0.3,
          managementPractices: 0.2
        },
        updatedAt: new Date(Date.now() - 86400000).toISOString(),
        updatedBy: 'admin@carbonready.com'
      } as T;
    }

    throw new Error('Mock data not available for this endpoint');
  }

  async getCarbonPosition(farmId: string): Promise<CarbonPosition> {
    return this.request<CarbonPosition>(`/v1/farms/${farmId}/carbon-position`);
  }

  async getCarbonReadinessIndex(farmId: string): Promise<CarbonReadinessIndex> {
    return this.request<CarbonReadinessIndex>(`/v1/farms/${farmId}/carbon-readiness-index`);
  }

  async getLatestSensorData(farmId: string): Promise<SensorData> {
    return this.request<SensorData>(`/v1/farms/${farmId}/sensor-data/latest`);
  }

  async getHistoricalTrends(farmId: string, days: number = 365): Promise<HistoricalTrends> {
    return this.request<HistoricalTrends>(`/v1/farms/${farmId}/historical-trends?days=${days}`);
  }

  async getCRIWeights(): Promise<CRIWeights> {
    return this.request<CRIWeights>('/v1/admin/cri-weights');
  }

  async updateCRIWeights(weights: {
    netCarbonPosition: number;
    socTrend: number;
    managementPractices: number;
  }): Promise<CRIWeights> {
    return this.request<CRIWeights>('/v1/admin/cri-weights', {
      method: 'PUT',
      body: JSON.stringify(weights),
    });
  }
}

export const api = new ApiClient();
