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
