# CarbonReady - Carbon Intelligence Platform

CarbonReady is an AI-powered carbon intelligence platform designed for smallholder cashew and coconut farms in Goa. The system enables farmers to measure and understand their farm-level carbon position through low-cost IoT sensing and AI-based biomass modeling.

## Architecture

The platform follows a three-tier serverless architecture:

1. **Edge Layer**: ESP32 sensors collect environmental data (soil moisture, soil temperature, air temperature, humidity)
2. **Cloud Layer**: AWS serverless services (IoT Core, Lambda, DynamoDB, S3) process data and perform carbon calculations
3. **Presentation Layer**: Web dashboard displays carbon intelligence insights

## Project Structure

```
.
├── app.py                      # CDK application entry point
├── cdk.json                    # CDK configuration
├── requirements.txt            # Python dependencies
├── cdk/
│   └── stacks/
│       ├── data_stack.py       # DynamoDB tables and S3 buckets
│       ├── iot_stack.py        # AWS IoT Core configuration
│       ├── compute_stack.py    # Lambda functions
│       ├── api_stack.py        # API Gateway and Cognito
│       └── monitoring_stack.py # CloudWatch and SNS
├── lambda/
│   ├── data_ingestion/         # Sensor data ingestion Lambda
│   ├── ai_processing/          # Carbon calculations Lambda
│   ├── farm_metadata_api/      # Farm metadata API Lambda
│   └── dashboard_api/          # Dashboard API Lambda
├── firmware/
│   └── esp32/                  # ESP32 sensor firmware
└── web-dashboard/              # React web dashboard (see web-dashboard/README.md)
    ├── src/
    │   ├── components/         # UI components
    │   ├── pages/              # Page components
    │   └── api.ts              # API client
    └── package.json
```

## Infrastructure Components

### DynamoDB Tables

1. **SensorData**: Stores sensor readings with 90-day TTL
2. **FarmMetadata**: Stores farm information with versioning
3. **CarbonCalculations**: Stores carbon calculation results (10-year retention)
4. **AIModelRegistry**: Stores AI model versions (10-year retention)
5. **SensorCalibration**: Stores sensor calibration events
6. **CRIWeights**: Stores Carbon Readiness Index weighting configuration

### S3 Bucket Structure

```
carbonready-sensor-data/
├── raw/                        # Raw sensor data (archived to Glacier after 1 year)
│   └── year=YYYY/month=MM/day=DD/
└── processed/                  # Processed carbon calculations
    └── year=YYYY/month=MM/
```

### Lambda Functions

1. **Data Ingestion**: Validates and stores sensor data from IoT Core
2. **AI Processing**: Performs carbon calculations (scheduled daily at 02:00 UTC)
3. **Farm Metadata API**: Handles farm metadata CRUD operations
4. **Dashboard API**: Serves carbon intelligence data to web dashboard

### API Endpoints

- `POST /api/v1/farms/{farmId}/metadata` - Create farm metadata
- `GET /api/v1/farms/{farmId}/metadata` - Get farm metadata
- `PUT /api/v1/farms/{farmId}/metadata` - Update farm metadata
- `GET /api/v1/farms/{farmId}/carbon-position` - Get carbon position
- `GET /api/v1/farms/{farmId}/carbon-readiness-index` - Get CRI with breakdown
- `GET /api/v1/farms/{farmId}/sensor-data/latest` - Get latest sensor readings
- `GET /api/v1/farms/{farmId}/historical-trends?days=365` - Get historical trends
- `GET /api/v1/admin/cri-weights` - Get CRI weights
- `PUT /api/v1/admin/cri-weights` - Update CRI weights (admin only)

## Prerequisites

- Python 3.12+
- AWS CLI configured with appropriate credentials
- AWS CDK CLI (`npm install -g aws-cdk`)
- Node.js 18+ (for CDK)

## Quick Start

### 1. Deploy Infrastructure

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

```bash
# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-ID/REGION

# Deploy all stacks
cdk deploy --all
```

### 2. Onboard a Farm

See [FARM_ONBOARDING.md](FARM_ONBOARDING.md) for complete onboarding guide.

```bash
# Automated onboarding (recommended)
python scripts/onboard_farm.py farm-001 esp32-001 \
  --crop-type coconut \
  --tree-age 15 \
  --tree-height 12.5

# Or follow manual steps in FARM_ONBOARDING.md
```

### 3. Access Dashboard

See [web-dashboard/README.md](web-dashboard/README.md) for dashboard setup.

```bash
cd web-dashboard
npm install
npm run dev
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Bootstrap CDK (first time only):
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

3. Deploy infrastructure:
```bash
cdk deploy --all
```

## Configuration

Set AWS account and region in `cdk.json` context:
```json
{
  "context": {
    "account": "123456789012",
    "region": "ap-south-1"
  }
}
```

Or pass as environment variables:
```bash
export CDK_DEFAULT_ACCOUNT=123456789012
export CDK_DEFAULT_REGION=ap-south-1
```

## Development

### Backend (CDK/Lambda)

Synthesize CloudFormation templates:
```bash
cdk synth
```

View differences before deployment:
```bash
cdk diff
```

Deploy specific stack:
```bash
cdk deploy CarbonReadyDataStack
```

Destroy infrastructure:
```bash
cdk destroy --all
```

### Web Dashboard

See [web-dashboard/README.md](web-dashboard/README.md) for detailed instructions.

Quick start:
```bash
cd web-dashboard
npm install
npm run dev
```

The dashboard will be available at `http://localhost:3000`

## Security

- **Device Authentication**: X.509 certificate-based authentication for ESP32 sensors
- **API Authentication**: Amazon Cognito with JWT tokens
- **Data Encryption**: TLS 1.2+ in transit, S3/DynamoDB encryption at rest
- **Data Integrity**: SHA-256 cryptographic hash verification for sensor data
- **Access Control**: IAM roles with least privilege, RBAC for API users

## Monitoring

- **CloudWatch Logs**: All Lambda functions log to CloudWatch with 1-year retention
- **SNS Topics**:
  - `carbonready-critical-alerts`: Lambda failures, data tampering, authentication failures
  - `carbonready-warnings`: Calibration expiry, data validation errors

## Cost Optimization

- Serverless architecture minimizes idle resource costs
- DynamoDB on-demand capacity for pilot phase flexibility
- S3 lifecycle policies archive data to Glacier after 1 year
- Lambda functions sized appropriately (512MB-2048MB)

## Scalability

Current capacity (pilot: 1-100 farms):
- IoT Core: 100 messages/second
- Lambda: 100 concurrent executions
- DynamoDB: On-demand capacity (auto-scaling)
- S3: Unlimited storage

## Documentation

### Deployment & Operations
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Infrastructure deployment guide
- **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)** - Production deployment checklist
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture details

### Farm Onboarding
- **[FARM_ONBOARDING.md](FARM_ONBOARDING.md)** - Complete farm onboarding guide
- **[ONBOARDING_CHECKLIST.md](ONBOARDING_CHECKLIST.md)** - Quick reference checklist
- **[DEVICE_PROVISIONING.md](DEVICE_PROVISIONING.md)** - ESP32 device provisioning

### Testing & Verification
- **[SETUP_AND_TEST_GUIDE.md](SETUP_AND_TEST_GUIDE.md)** - Setup and testing guide
- **[TEST_RESULTS_SUMMARY.md](TEST_RESULTS_SUMMARY.md)** - Test results summary
- **[TESTING_COMMANDS.md](TESTING_COMMANDS.md)** - Common testing commands

### Security & Compliance
- **[SECURITY.md](SECURITY.md)** - Security best practices
- **[PRE_COMMIT_CHECKLIST.md](PRE_COMMIT_CHECKLIST.md)** - Pre-commit checklist

### Component-Specific
- **[web-dashboard/README.md](web-dashboard/README.md)** - Web dashboard setup
- **[firmware/esp32/README.md](firmware/esp32/README.md)** - ESP32 firmware guide
- **[lambda/*/README.md](lambda/)** - Lambda function documentation

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the CarbonReady development team.
