import type {
  CarbonPosition,
  CarbonReadinessIndex,
  SensorData,
  HistoricalTrends,
  CRIWeights,
  FarmMetadata,
  ApiError
} from './types';
import { fetchAuthSession } from 'aws-amplify/auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true';

class ApiClient {
  private async getAuthHeaders(): Promise<Record<string, string>> {
    try {
      const session = await fetchAuthSession();
      const idToken = session.tokens?.idToken?.toString();
      
      if (idToken) {
        return {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json',
        };
      }
    } catch (error) {
      console.error('Error getting auth token:', error);
    }
    
    return {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    // Use mock data if enabled
    if (USE_MOCK_DATA) {
      return this.getMockData<T>(endpoint);
    }

    const url = `${API_BASE_URL}${endpoint}`;
    const headers = await this.getAuthHeaders();
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...headers,
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
      // Realistic data for a 5-hectare coconut farm in Goa
      // Coconut farms are typically carbon sinks due to high biomass
      const calculatedAt = new Date(Date.now() - 900000).toISOString(); // 15 min ago (sensor interval)
      const isStale = Date.now() - new Date(calculatedAt).getTime() > 24 * 60 * 60 * 1000;
      
      return {
        farmId: 'farm-001',
        netCarbonPosition: 2847.50, // Positive = carbon sink (realistic for coconut)
        classification: 'Net Carbon Sink',
        annualSequestration: 3450.75, // ~690 kg CO2e per hectare for coconut
        emissions: {
          fertilizerEmissions: 425.50, // Organic farming, minimal fertilizer
          irrigationEmissions: 177.75, // Drip irrigation, low energy
          totalEmissions: 603.25,
          unit: 'kg CO2e/year'
        },
        carbonStock: 75000, // Above-ground biomass: 625 trees × 120 kg C/tree
        co2EquivalentStock: 275250, // 75,000 kg C × 3.67 = 275,250 kg CO2e
        calculatedAt,
        isStale,
        unit: 'kg CO2e/year'
      } as T;
    }

    if (endpoint.includes('/carbon-readiness-index')) {
      return {
        farmId: 'farm-001',
        carbonReadinessIndex: {
          score: 78.5, // Good score for pilot farm
          classification: 'Excellent',
          components: {
            netCarbonPosition: {
              score: 88, // Strong carbon sink
              weight: 0.5,
              contribution: 44.0
            },
            socTrend: {
              score: 72, // Improving soil organic carbon
              weight: 0.3,
              contribution: 21.6
            },
            managementPractices: {
              score: 65, // Good practices, room for improvement
              weight: 0.2,
              contribution: 13.0
            }
          },
          scoringLogicVersion: 'v1.0.0',
          calculatedAt: new Date(Date.now() - 900000).toISOString() // 15 min ago
        },
        socTrend: {
          status: 'Improving',
          score: 0.18, // Positive trend
          biomassReturn: 14.2, // Good organic matter return
          managementScore: 0.72,
          dataSpanDays: 90 // 3 months of pilot data
        },
        netCarbonPosition: 2847.50
      } as T;
    }

    if (endpoint.includes('/sensor-data/latest')) {
      // Realistic sensor data for Goa climate (tropical coastal)
      // Data from 15 minutes ago (sensor sends every 15 min)
      const timestamp = new Date(Date.now() - 900000).toISOString();
      
      return {
        farmId: 'farm-001',
        deviceId: 'esp32-farm-001',
        timestamp: timestamp,
        readings: {
          soilMoisture: 52.3,  // Good moisture for coconut (45-60% optimal)
          soilTemperature: 26.8,  // Typical for Goa laterite soil
          airTemperature: 31.2,  // Goa daytime temperature
          humidity: 78.5  // High humidity typical for coastal Goa
        },
        validationStatus: 'valid'
      } as T;
    }

    if (endpoint.includes('/historical-trends')) {
      // Generate 90 days of realistic pilot data (3 months)
      const trends = [];
      const now = Date.now();
      const daysOfData = 90; // Pilot phase: 3 months
      
      for (let i = daysOfData - 1; i >= 0; i--) {
        const date = new Date(now - i * 24 * 60 * 60 * 1000);
        
        // Simulate seasonal variation for Goa
        // Monsoon season (June-Sept): higher sequestration, lower emissions
        const month = date.getMonth();
        const isMonsoon = month >= 5 && month <= 8;
        
        // Base values for coconut farm
        const baseSequestration = 3450;
        const baseEmissions = 600;
        
        // Add realistic variation
        const seasonalFactor = isMonsoon ? 1.15 : 0.95; // Higher growth in monsoon
        const randomVariation = 0.9 + Math.random() * 0.2; // ±10% daily variation
        
        const sequestration = baseSequestration * seasonalFactor * randomVariation;
        const emissions = baseEmissions * (isMonsoon ? 0.85 : 1.05) * randomVariation; // Lower irrigation in monsoon
        
        // CRI improves over time as practices improve
        const criImprovement = Math.min(10, i / 9); // Up to 10 point improvement
        const baseCRI = 68;
        
        trends.push({
          date: date.toISOString().split('T')[0],
          netCarbonPosition: sequestration - emissions,
          annualSequestration: sequestration,
          totalEmissions: emissions,
          carbonReadinessIndex: baseCRI + criImprovement + (Math.random() * 4 - 2), // Some noise
          socTrend: i < 30 ? 'Improving' : i < 60 ? 'Stable' : 'Improving'
        });
      }
      
      return {
        farmId: 'farm-001',
        days: daysOfData,
        dataPoints: trends.length,
        trends: trends.reverse() // Oldest to newest
      } as T;
    }

    if (endpoint.includes('/farm-metadata')) {
      return {
        farmId: 'farm-001',
        farmName: 'Pilot Farm - Goa',
        location: 'Ponda, Goa, India',
        cropType: 'coconut',
        farmSizeHectares: 5.0,
        soilType: 'laterite', // Common in Goa
        irrigationType: 'drip',
        ownerName: 'Farm Owner',
        registeredDate: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 90 days ago
        deviceIds: ['esp32-farm-001'],
        coordinates: {
          latitude: 15.4909, // Ponda, Goa
          longitude: 74.0120
        },
        additionalInfo: {
          treeCount: 625, // ~125 trees per hectare for coconut
          averageTreeAge: 15, // Mature productive trees
          plantingYear: 2010,
          certifications: ['Organic (in progress)'],
          notes: 'Pilot deployment - Phase 1. Sensors installed 3 months ago. Baseline data collection complete.'
        }
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

  async getFarmMetadata(farmId: string): Promise<FarmMetadata> {
    return this.request<FarmMetadata>(`/v1/farm-metadata/${farmId}`);
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
