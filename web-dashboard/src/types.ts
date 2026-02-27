export interface CarbonPosition {
  farmId: string;
  netCarbonPosition: number;
  annualSequestration: number;
  emissions: {
    fertilizerEmissions: number;
    irrigationEmissions: number;
    totalEmissions: number;
    unit: string;
  };
  classification: 'Net Carbon Sink' | 'Net Carbon Source';
  carbonStock: number;
  co2EquivalentStock: number;
  calculatedAt: string;
  isStale: boolean;
  unit: string;
}

export interface CarbonReadinessIndex {
  farmId: string;
  carbonReadinessIndex: {
    score: number;
    classification: 'Excellent' | 'Moderate' | 'Needs Improvement';
    components: {
      netCarbonPosition: {
        score: number;
        weight: number;
        contribution: number;
      };
      socTrend: {
        score: number;
        weight: number;
        contribution: number;
      };
      managementPractices: {
        score: number;
        weight: number;
        contribution: number;
      };
    };
    scoringLogicVersion: string;
    calculatedAt: string;
  };
  socTrend: {
    status: 'Improving' | 'Stable' | 'Declining' | 'Insufficient Data';
    score?: number;
    biomassReturn?: number;
    managementScore?: number;
    dataSpanDays?: number;
  };
  netCarbonPosition: number;
}

export interface SensorData {
  farmId: string;
  deviceId: string;
  timestamp: string;
  readings: {
    soilMoisture: number;
    soilTemperature: number;
    airTemperature: number;
    humidity: number;
  };
  validationStatus: string;
}

export interface HistoricalTrend {
  date: string;
  netCarbonPosition: number;
  annualSequestration: number;
  totalEmissions: number;
  carbonReadinessIndex?: number;
  socTrend?: string;
}

export interface HistoricalTrends {
  farmId: string;
  days: number;
  dataPoints: number;
  trends: HistoricalTrend[];
}

export interface CRIWeights {
  configId: string;
  version: number;
  weights: {
    netCarbonPosition: number;
    socTrend: number;
    managementPractices: number;
  };
  updatedAt: string | null;
  updatedBy: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    timestamp: string;
  };
}
