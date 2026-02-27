# AI Processing Lambda

This Lambda function performs carbon calculations for CarbonReady farms on a scheduled basis.

## Modules

### biomass_calculator.py

Core module for biomass and carbon calculations.

#### Functions

**Biomass Calculation:**
- `calculate_cashew_biomass(dbh_cm, age_years)` - Calculate per-tree biomass for cashew using DBH and age
- `calculate_coconut_biomass(height_m, age_years)` - Calculate per-tree biomass for coconut using height and age
- `calculate_farm_biomass(metadata)` - Calculate total farm biomass by scaling per-tree biomass

**Carbon Conversion:**
- `convert_biomass_to_co2e(biomass_kg)` - Central conversion function: biomass → carbon → CO₂e

**Annual Sequestration:**
- `estimate_sequestration_from_growth_curves(tree_age, crop_type, region, dynamodb_client)` - Estimate annual biomass increment using Chapman-Richards growth curves
- `calculate_annual_sequestration(farm_id, metadata, historical_biomass, dynamodb_client)` - Calculate annual carbon sequestration using historical data or growth curves

**Growth Curve Support:**
- `load_growth_curve_parameters(crop_type, region, dynamodb)` - Load regional growth curve parameters from DynamoDB
- `get_default_growth_parameters(crop_type)` - Get default Chapman-Richards parameters for crop type
- `calculate_chapman_richards_biomass(age, parameters)` - Calculate biomass using Chapman-Richards model

## Growth Curve Model

The system uses the Chapman-Richards growth curve model to estimate biomass when historical data is unavailable:

```
Biomass(t) = a × (1 - exp(-b × t))^c
```

Where:
- `a`: Maximum biomass asymptote (kg)
- `b`: Growth rate parameter
- `c`: Shape parameter
- `t`: Tree age in years

### Default Parameters

**Cashew (Goa region):**
- a = 250.0 kg
- b = 0.08
- c = 1.5

**Coconut (Goa region):**
- a = 350.0 kg
- b = 0.06
- c = 1.8

## Annual Sequestration Calculation

The system calculates annual carbon sequestration using two methods:

1. **Historical Method (Preferred):** When previous year's biomass data is available, calculate the difference between current and historical biomass
2. **Growth Curve Method (Fallback):** When historical data is unavailable, estimate biomass increment using Chapman-Richards growth curves

The biomass increment is then converted to CO₂e using the central `convert_biomass_to_co2e()` function.

## DynamoDB Tables

### GrowthCurvesTable

Stores regional growth curve parameters for sequestration estimation.

**Schema:**
- Partition Key: `cropType` (String) - "cashew" or "coconut"
- Sort Key: `region` (String) - Region name (e.g., "Goa")

**Attributes:**
- `growthCurve` (Map):
  - `model` (String) - "Chapman-Richards"
  - `parameters` (Map):
    - `a` (Number) - Maximum biomass asymptote
    - `b` (Number) - Growth rate parameter
    - `c` (Number) - Shape parameter
  - `description` (String)
  - `source` (String)
  - `calibrationDate` (String, ISO8601)

## Initialization

To initialize growth curve parameters in DynamoDB:

```bash
python scripts/init_growth_curves.py
```

This will populate the GrowthCurvesTable with default parameters for cashew and coconut crops in the Goa region.

## Testing

Run unit tests:

```bash
python -m pytest lambda/ai_processing/test_biomass_calculator.py -v
```

Test coverage includes:
- Biomass calculation for cashew and coconut
- Farm-level biomass scaling
- CO₂e conversion
- Growth curve parameter loading
- Chapman-Richards biomass calculation
- Annual sequestration with historical data
- Annual sequestration with growth curves
- Edge case handling

## Environment Variables

- `FARM_METADATA_TABLE` - DynamoDB table for farm metadata
- `CARBON_CALCULATIONS_TABLE` - DynamoDB table for carbon calculation results
- `AI_MODEL_REGISTRY_TABLE` - DynamoDB table for AI model versions
- `CRI_WEIGHTS_TABLE` - DynamoDB table for CRI weights
- `SENSOR_DATA_TABLE` - DynamoDB table for sensor data
- `GROWTH_CURVES_TABLE` - DynamoDB table for growth curve parameters

## Requirements

Validates the following requirements:
- 4.1, 4.2, 4.3: Biomass estimation using allometric equations
- 5.1, 5.2, 5.3: Carbon stock and CO₂ equivalent calculation
- 8.1, 8.2, 8.3: Annual sequestration calculation using historical data or growth curves


## AI Processing Pipeline (index.py)

### Overview

The AI Processing Pipeline orchestrates the complete carbon intelligence calculation workflow for all farms in the system.

### Trigger

- **EventBridge Scheduled Rule**: Runs daily at 02:00 UTC
- Processes up to 100 farms in pilot phase
- Configured in `cdk/stacks/compute_stack.py`

### Main Functions

#### `lambda_handler(event, context)`
Main entry point triggered by EventBridge. Processes all farms and returns summary results.

**Returns:**
```json
{
  "status": "success",
  "processed": 10,
  "results": [...]
}
```

#### `process_farm_carbon(farm_id)`
Core orchestration function that performs all carbon calculations for a single farm.

**Workflow:**
1. Retrieve farm metadata from DynamoDB
2. Retrieve historical biomass data (if available)
3. Calculate aboveground biomass
4. Calculate carbon stock and CO₂ equivalent
5. Calculate annual sequestration increment
6. Analyze SOC trend (stub - Task 10 optional)
7. Calculate emissions from fertilizer and irrigation
8. Compute net carbon position
9. Generate Carbon Readiness Index
10. Store results with model version metadata
11. Set retention timestamp to +10 years

**Validates Requirements**: 4.1, 4.2, 4.3, 5.1, 5.2, 6.1, 7.1, 8.1, 8.4, 9.1, 19.3, 19.4, 19.8

#### `get_all_farms()`
Scans FarmMetadata table to get list of all farm IDs (up to 100 for pilot).

#### `get_farm_metadata(farm_id)`
Retrieves latest version of farm metadata from DynamoDB.

#### `get_historical_biomass(farm_id)`
Retrieves previous biomass calculation for sequestration estimation.

#### `analyze_soc_trend_stub(farm_id, metadata)`
Stub for SOC trend analysis. Returns "Insufficient Data" status.
Full implementation is in Task 10 (optional).

#### `store_carbon_calculation(calculation_result)`
Stores calculation results in DynamoDB with 10-year retention timestamp.

#### `convert_floats_to_decimal(obj)`
Recursively converts float values to Decimal for DynamoDB compatibility.

### Model Versions

Current model versions tracked with each calculation:
```python
MODEL_VERSIONS = {
    "biomass": "v1.0.0",
    "sequestration": "v1.0.0",
    "emissions": "v1.0.0",
    "soc": "v1.0.0",
    "cri": "v1.0.0"
}
```

### Output Schema

Each calculation result stored in DynamoDB contains:

```json
{
  "farmId": "string",
  "timestamp": "number (Unix epoch)",
  "calculatedAt": "ISO8601",
  "biomass": "number (kg)",
  "carbonStock": "number (kg)",
  "co2EquivalentStock": "number (kg CO2e)",
  "annualSequestration": "number (kg CO2e/year)",
  "sequestrationMethod": "historical | growth_curve",
  "emissions": "number (kg CO2e/year)",
  "emissionsBreakdown": {
    "fertilizer": "number",
    "irrigation": "number"
  },
  "netCarbonPosition": "number (kg CO2e/year)",
  "netCarbonClassification": "Net Carbon Sink | Net Carbon Source",
  "socTrend": "Improving | Stable | Declining | Insufficient Data",
  "carbonReadinessIndex": "number (0-100)",
  "criClassification": "Needs Improvement | Moderate | Excellent",
  "criComponents": {
    "netCarbonPosition": "number",
    "socTrend": "number",
    "managementPractices": "number"
  },
  "criWeights": {
    "netCarbonPosition": "number",
    "socTrend": "number",
    "managementPractices": "number"
  },
  "modelVersions": {
    "biomass": "string",
    "sequestration": "string",
    "emissions": "string",
    "soc": "string",
    "cri": "string"
  },
  "retentionUntil": "ISO8601 (+10 years)"
}
```

### Testing

Run the complete pipeline test:

```bash
python lambda/ai_processing/test_ai_processing.py
```

The test validates:
- Complete carbon calculation workflow
- Biomass calculation for cashew and coconut
- Sequestration estimation using growth curves
- Emissions calculation with IPCC factors
- Net carbon position computation
- Carbon Readiness Index generation
- DynamoDB Decimal conversion

### Performance

- **Memory**: 2048 MB
- **Timeout**: 5 minutes
- **Concurrency**: 10 (batch processing)
- **Processing Time**: ~3 seconds per farm (target: 100 farms in 5 minutes)

### Error Handling

- Graceful fallback to default values if DynamoDB tables unavailable
- Individual farm errors logged but don't stop batch processing
- All errors logged to CloudWatch with full context
- Returns summary with success/error status for each farm
