# Dashboard API Lambda

## Overview

The Dashboard API Lambda serves carbon intelligence data to the web dashboard. It provides endpoints for retrieving carbon position, Carbon Readiness Index (CRI), sensor data, and historical trends.

## Authentication & Authorization

### JWT Token Validation

All API endpoints require authentication via Amazon Cognito JWT tokens. The API Gateway validates JWT tokens before forwarding requests to the Lambda function.

**Authentication Flow:**
1. User authenticates with Cognito User Pool
2. Cognito returns JWT access token
3. Client includes token in `Authorization` header: `Bearer <token>`
4. API Gateway validates token with Cognito
5. If valid, request is forwarded to Lambda with user claims

### Role-Based Access Control (RBAC)

The system implements two user roles:

#### Farmer Role
- Can view their own farm data
- Access to all GET endpoints for their farm
- Cannot modify CRI weights

#### Admin Role
- Can view all farm data
- Can modify CRI weights via PUT /api/v1/admin/cri-weights
- Full system access

**Authorization Check:**
- Authentication is enforced at API Gateway level (all endpoints)
- Admin role check is performed in Lambda function for admin endpoints
- Unauthorized attempts are logged for security auditing

## API Endpoints

### GET /api/v1/farms/{farmId}/carbon-position

Returns the latest carbon position for a farm.

**Response:**
```json
{
  "farmId": "farm-001",
  "netCarbonPosition": 1250.50,
  "annualSequestration": 2000.00,
  "emissions": {
    "fertilizerEmissions": 500.00,
    "irrigationEmissions": 249.50,
    "totalEmissions": 749.50
  },
  "classification": "Net Carbon Sink",
  "carbonStock": 5000.00,
  "co2EquivalentStock": 18335.00,
  "calculatedAt": "2025-01-15T10:30:00Z",
  "isStale": false,
  "unit": "kg CO2e/year"
}
```

### GET /api/v1/farms/{farmId}/carbon-readiness-index

Returns the Carbon Readiness Index with full breakdown showing component contributions and weights.

**Response:**
```json
{
  "farmId": "farm-001",
  "carbonReadinessIndex": {
    "score": 72.5,
    "classification": "Excellent",
    "components": {
      "netCarbonPosition": {
        "score": 85,
        "weight": 0.5,
        "contribution": 42.5
      },
      "socTrend": {
        "score": 60,
        "weight": 0.3,
        "contribution": 18.0
      },
      "managementPractices": {
        "score": 60,
        "weight": 0.2,
        "contribution": 12.0
      }
    },
    "scoringLogicVersion": "v1.0.0",
    "calculatedAt": "2025-01-15T10:30:00Z"
  },
  "socTrend": {
    "status": "Stable",
    "score": 0.02
  },
  "netCarbonPosition": 1250.50
}
```

### GET /api/v1/farms/{farmId}/sensor-data/latest

Returns the most recent sensor readings for a farm.

**Response:**
```json
{
  "farmId": "farm-001",
  "deviceId": "esp32-abc123",
  "timestamp": "2025-01-15T14:45:00Z",
  "readings": {
    "soilMoisture": 45.5,
    "soilTemperature": 24.3,
    "airTemperature": 28.7,
    "humidity": 65.2
  },
  "validationStatus": "valid"
}
```

### GET /api/v1/farms/{farmId}/historical-trends?days=365

Returns historical carbon trends for the specified time period.

**Query Parameters:**
- `days` (optional): Number of days to retrieve (1-365, default: 365)

**Response:**
```json
{
  "farmId": "farm-001",
  "days": 365,
  "dataPoints": 52,
  "trends": [
    {
      "date": "2024-01-15T10:30:00Z",
      "netCarbonPosition": 1100.00,
      "annualSequestration": 1800.00,
      "totalEmissions": 700.00,
      "carbonReadinessIndex": 68.5,
      "socTrend": "Stable"
    }
  ]
}
```

### GET /api/v1/admin/cri-weights

Returns the current CRI weighting configuration.

**Response:**
```json
{
  "configId": "default",
  "version": 1,
  "weights": {
    "netCarbonPosition": 0.5,
    "socTrend": 0.3,
    "managementPractices": 0.2
  },
  "updatedAt": "2025-01-15T10:00:00Z",
  "updatedBy": "admin-user"
}
```

### PUT /api/v1/admin/cri-weights

Updates CRI weights (admin only).

**Request Body:**
```json
{
  "netCarbonPosition": 0.5,
  "socTrend": 0.3,
  "managementPractices": 0.2
}
```

**Validation:**
- All three weight components must be provided
- Weights must be non-negative numbers
- Weights must sum to 1.0 (100%)
- User must have admin role

**Response:**
```json
{
  "configId": "default",
  "version": 2,
  "weights": {
    "netCarbonPosition": 0.5,
    "socTrend": 0.3,
    "managementPractices": 0.2
  },
  "updatedAt": "2025-01-15T11:00:00Z",
  "updatedBy": "admin-user",
  "message": "CRI weights updated successfully"
}
```

## Error Handling

All errors follow a standardized format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "timestamp": "2025-01-15T10:30:00Z",
    "details": {
      "field": "fieldName",
      "expected": "expectedValue",
      "received": "receivedValue"
    }
  }
}
```

### Error Codes

- `ENDPOINT_NOT_FOUND` (404): Requested endpoint does not exist
- `NO_DATA` (404): No data found for the requested farm
- `NO_CRI_DATA` (404): CRI not yet calculated for the farm
- `INVALID_INPUT` (400): Invalid input parameters
- `INVALID_DAYS` (400): Days parameter out of range (1-365)
- `INVALID_WEIGHTS` (400): Missing weight components
- `INVALID_WEIGHT_VALUE` (400): Weight value is not a valid number
- `INVALID_WEIGHT_SUM` (400): Weights do not sum to 1.0
- `UNAUTHORIZED` (403): Admin privileges required
- `QUERY_ERROR` (500): Database query failed
- `UPDATE_ERROR` (500): Database update failed
- `INTERNAL_ERROR` (500): Unexpected server error

## Security Features

### Data Integrity
- All sensor data includes SHA-256 cryptographic hash
- Hash verification performed at ingestion
- Tampering attempts logged and alerted

### Access Control
- JWT token validation at API Gateway
- Role-based authorization in Lambda
- Unauthorized attempts logged for audit

### Data Staleness
- Carbon position endpoint includes `isStale` flag
- Data older than 24 hours marked as stale
- Helps users identify outdated information

## Environment Variables

- `CARBON_CALCULATIONS_TABLE`: DynamoDB table for carbon calculations
- `SENSOR_DATA_TABLE`: DynamoDB table for sensor data
- `CRI_WEIGHTS_TABLE`: DynamoDB table for CRI weights configuration

## Dependencies

- `boto3>=1.34.0`: AWS SDK for Python

## Testing

Run unit tests:
```bash
pytest lambda/dashboard_api/test_dashboard_api.py
```

## Deployment

The Lambda function is deployed via AWS CDK:
```bash
cdk deploy ApiStack
```

## Monitoring

- CloudWatch Logs: All errors and unauthorized attempts logged
- CloudWatch Metrics: Invocation count, duration, errors
- X-Ray Tracing: End-to-end request tracing enabled
