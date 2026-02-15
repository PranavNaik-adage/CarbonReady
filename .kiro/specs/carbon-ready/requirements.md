# Requirements Document: CarbonReady

## Introduction

CarbonReady is an AI-powered carbon intelligence platform designed for smallholder cashew and coconut farms in Goa. The system enables farmers to measure and understand their farm-level carbon position through low-cost IoT sensing and AI-based biomass modeling. The platform collects environmental data from ESP32 sensors, processes farm metadata, and generates carbon intelligence insights including sequestration estimates, emissions calculations, and sustainability metrics. This pilot deployment focuses on carbon readiness and sustainability intelligence without carbon credit trading functionality.

## Glossary

- **CarbonReady_System**: The complete AI-powered carbon intelligence platform including edge devices, cloud infrastructure, and user interfaces
- **ESP32_Sensor**: Low-cost IoT edge device that collects environmental data from farm locations
- **Farm_Metadata**: Farmer-provided information including tree age, height, DBH, density, fertilizer usage, and irrigation activity
- **Aboveground_Biomass**: The total mass of living plant material above the soil surface, measured in kilograms
- **Carbon_Stock**: The amount of carbon stored in biomass, calculated as Biomass × 0.5
- **CO2_Equivalent**: The amount of CO₂ that would have the same global warming impact, calculated as Carbon × 3.667
- **Soil_Organic_Carbon**: Carbon stored in soil organic matter, tracked over time
- **Net_Carbon_Position**: The difference between annual carbon sequestration increment and annual emissions (Annual_Sequestration_Increment − Annual_Emissions)
- **Annual_Sequestration_Increment**: The amount of carbon sequestered by the farm in one year, calculated from biomass growth
- **Carbon_Readiness_Index**: A composite metric indicating farm sustainability based on carbon position and management practices
- **Allometric_Equation**: Crop-specific mathematical formula relating tree dimensions to biomass
- **IPCC_Factor**: Emission factors published by the Intergovernmental Panel on Climate Change
- **DBH**: Diameter at Breast Height, a standard measurement for tree trunk diameter
- **AWS_IoT_Core**: Amazon Web Services IoT message broker and device management service
- **Data_Ingestion_Pipeline**: The system component that receives and validates sensor data
- **AI_Processing_Pipeline**: The system component that performs biomass modeling and carbon calculations
- **Dashboard**: Web-based user interface displaying carbon intelligence insights

## Requirements

### Requirement 1: Environmental Data Collection

**User Story:** As a farmer, I want the system to automatically collect environmental data from my farm, so that I can monitor conditions without manual effort.

#### Acceptance Criteria

1. WHEN an ESP32_Sensor is deployed on a farm, THE CarbonReady_System SHALL collect soil moisture readings at intervals not exceeding 15 minutes
2. WHEN an ESP32_Sensor is deployed on a farm, THE CarbonReady_System SHALL collect soil temperature readings at intervals not exceeding 15 minutes
3. WHEN an ESP32_Sensor is deployed on a farm, THE CarbonReady_System SHALL collect air temperature readings at intervals not exceeding 15 minutes
4. WHEN an ESP32_Sensor is deployed on a farm, THE CarbonReady_System SHALL collect humidity readings at intervals not exceeding 15 minutes
5. WHEN sensor readings are collected, THE CarbonReady_System SHALL timestamp each reading with UTC time
6. WHEN sensor readings are collected, THE CarbonReady_System SHALL associate each reading with the correct farm identifier

### Requirement 2: Farm Metadata Management

**User Story:** As a farmer, I want to input information about my farm and trees, so that the system can accurately estimate carbon levels.

#### Acceptance Criteria

1. WHEN a farmer provides farm metadata, THE CarbonReady_System SHALL accept tree age values in years
2. WHEN a farmer provides farm metadata for coconut trees, THE CarbonReady_System SHALL accept tree height values in meters
3. WHEN a farmer provides farm metadata for cashew trees, THE CarbonReady_System SHALL accept DBH values in centimeters
4. WHEN a farmer provides farm metadata, THE CarbonReady_System SHALL accept plantation density values in trees per hectare
5. WHEN a farmer provides farm metadata, THE CarbonReady_System SHALL accept fertilizer usage values in kilograms per hectare per year
6. WHEN a farmer provides farm metadata, THE CarbonReady_System SHALL accept irrigation activity values in liters per hectare per year
7. WHEN farm metadata is submitted, THE CarbonReady_System SHALL validate that all required fields contain values within acceptable ranges
8. IF farm metadata validation fails, THEN THE CarbonReady_System SHALL return descriptive error messages indicating which fields are invalid

### Requirement 3: Data Ingestion and Storage

**User Story:** As a system administrator, I want sensor data to be securely transmitted and stored, so that the platform can process it reliably.

#### Acceptance Criteria

1. WHEN an ESP32_Sensor transmits data, THE CarbonReady_System SHALL authenticate the device using AWS_IoT_Core certificate-based authentication
2. WHEN sensor data is received by AWS_IoT_Core, THE Data_Ingestion_Pipeline SHALL validate the data format and completeness
3. IF sensor data validation fails, THEN THE Data_Ingestion_Pipeline SHALL log the error and discard the invalid data
4. WHEN valid sensor data is received, THE Data_Ingestion_Pipeline SHALL store the data in DynamoDB within 5 seconds
5. WHEN valid sensor data is received, THE Data_Ingestion_Pipeline SHALL archive raw data to S3 for long-term storage
6. WHEN farm metadata is submitted, THE CarbonReady_System SHALL store it in DynamoDB with versioning support

### Requirement 4: Biomass Estimation

**User Story:** As a farmer, I want the system to estimate how much biomass my trees contain, so that I can understand my farm's carbon potential.

#### Acceptance Criteria

1. WHEN calculating biomass for coconut trees, THE AI_Processing_Pipeline SHALL apply the coconut-specific Allometric_Equation using tree height and age
2. WHEN calculating biomass for cashew trees, THE AI_Processing_Pipeline SHALL apply the cashew-specific Allometric_Equation using DBH and age
3. WHEN biomass is calculated, THE AI_Processing_Pipeline SHALL multiply by plantation density to obtain total farm Aboveground_Biomass
4. WHEN Aboveground_Biomass is calculated, THE AI_Processing_Pipeline SHALL store the result in kilograms with precision to two decimal places
5. WHEN tree parameters are updated, THE AI_Processing_Pipeline SHALL recalculate Aboveground_Biomass within 60 seconds

### Requirement 5: Carbon Stock Calculation

**User Story:** As a farmer, I want to know how much carbon my farm stores, so that I can understand my contribution to carbon sequestration.

#### Acceptance Criteria

1. WHEN Aboveground_Biomass is available, THE AI_Processing_Pipeline SHALL calculate Carbon_Stock by multiplying Aboveground_Biomass by 0.5
2. WHEN Carbon_Stock is calculated, THE AI_Processing_Pipeline SHALL calculate CO2_Equivalent by multiplying Carbon_Stock by 3.667
3. WHEN carbon calculations are complete, THE AI_Processing_Pipeline SHALL store Carbon_Stock and CO2_Equivalent values with precision to two decimal places
4. WHEN carbon calculations are complete, THE AI_Processing_Pipeline SHALL timestamp the calculation with UTC time

### Requirement 6: Soil Organic Carbon Analysis

**User Story:** As a farmer, I want to track soil carbon levels over time, so that I can see if my soil health is improving.

#### Acceptance Criteria

1. WHEN estimating Soil_Organic_Carbon trends, THE AI_Processing_Pipeline SHALL use proxy modeling that combines biomass return data, management practices, regional baseline SOC values, and environmental context
2. WHEN calculating biomass return, THE AI_Processing_Pipeline SHALL estimate organic matter returned to soil from leaf litter, pruning, and crop residues
3. WHEN analyzing management practices, THE AI_Processing_Pipeline SHALL incorporate fertilizer usage, irrigation activity, and tillage practices into the SOC model
4. WHEN regional baseline data is available, THE AI_Processing_Pipeline SHALL calibrate the SOC model using regional baseline SOC values for similar soil types and climates
5. WHEN determining Soil_Organic_Carbon trend classification, THE AI_Processing_Pipeline SHALL require a minimum of 90 days of environmental and management data
6. IF less than 90 days of data is available, THEN THE AI_Processing_Pipeline SHALL indicate "Insufficient Data" status
7. WHEN sufficient data is available and Soil_Organic_Carbon trend is determined, THE AI_Processing_Pipeline SHALL classify the trend as "Improving", "Stable", or "Declining"

### Requirement 7: Emissions Calculation

**User Story:** As a farmer, I want to understand emissions from my farming activities, so that I can identify opportunities to reduce my carbon footprint.

#### Acceptance Criteria

1. WHEN fertilizer usage data is available, THE AI_Processing_Pipeline SHALL calculate fertilizer-related emissions using IPCC_Factor values
2. WHEN irrigation activity data is available, THE AI_Processing_Pipeline SHALL calculate irrigation-related emissions using IPCC_Factor values
3. WHEN emissions are calculated, THE AI_Processing_Pipeline SHALL express total emissions in CO2_Equivalent kilograms per year
4. WHEN emissions calculations are complete, THE AI_Processing_Pipeline SHALL store the results with precision to two decimal places

### Requirement 8: Net Carbon Position Computation

**User Story:** As a farmer, I want to see my overall carbon balance, so that I can understand if my farm is a net carbon sink or source.

#### Acceptance Criteria

1. WHEN calculating annual sequestration, THE AI_Processing_Pipeline SHALL estimate Annual_Sequestration_Increment based on biomass growth over the past year
2. IF historical biomass data is unavailable, THEN THE AI_Processing_Pipeline SHALL estimate Annual_Sequestration_Increment using crop-specific growth curves calibrated to tree age and regional averages
3. WHEN Annual_Sequestration_Increment is calculated, THE AI_Processing_Pipeline SHALL express the result in CO2_Equivalent kilograms per year
4. WHEN both Annual_Sequestration_Increment and annual emissions data are available, THE AI_Processing_Pipeline SHALL calculate Net_Carbon_Position as Annual_Sequestration_Increment minus annual emissions
5. WHEN Net_Carbon_Position is positive, THE AI_Processing_Pipeline SHALL classify the farm as a "Net Carbon Sink"
6. WHEN Net_Carbon_Position is negative, THE AI_Processing_Pipeline SHALL classify the farm as a "Net Carbon Source"
7. WHEN Net_Carbon_Position is calculated, THE AI_Processing_Pipeline SHALL store the value in CO2_Equivalent kilograms per year

### Requirement 9: Carbon Readiness Index

**User Story:** As a farmer, I want a simple score that shows my farm's sustainability, so that I can track my progress over time.

#### Acceptance Criteria

1. WHEN Net_Carbon_Position, Soil_Organic_Carbon trend, and management practices data are available, THE AI_Processing_Pipeline SHALL calculate the Carbon_Readiness_Index using configurable weighting parameters
2. WHEN Carbon_Readiness_Index weighting parameters are not specified, THE AI_Processing_Pipeline SHALL use default weights of 50% for Net_Carbon_Position, 30% for Soil_Organic_Carbon trend, and 20% for sustainable management practices
3. WHEN Carbon_Readiness_Index weighting parameters are provided, THE AI_Processing_Pipeline SHALL validate that weights sum to 100%
4. IF Carbon_Readiness_Index weighting parameters do not sum to 100%, THEN THE AI_Processing_Pipeline SHALL return an error and use default weights
5. WHEN a user attempts to modify Carbon_Readiness_Index weighting parameters, THE CarbonReady_System SHALL verify that the user has authorized administrative privileges
6. IF a user without administrative privileges attempts to modify weighting parameters, THEN THE CarbonReady_System SHALL reject the request and log the unauthorized attempt
7. WHEN Carbon_Readiness_Index is calculated, THE AI_Processing_Pipeline SHALL normalize the score to a range of 0 to 100
8. WHEN Carbon_Readiness_Index is below 40, THE AI_Processing_Pipeline SHALL classify the farm as "Needs Improvement"
9. WHEN Carbon_Readiness_Index is between 40 and 70, THE AI_Processing_Pipeline SHALL classify the farm as "Moderate"
10. WHEN Carbon_Readiness_Index is above 70, THE AI_Processing_Pipeline SHALL classify the farm as "Excellent"

### Requirement 10: Dashboard Visualization

**User Story:** As a farmer, I want to view my carbon intelligence insights in a simple dashboard, so that I can make informed decisions about my farm management.

#### Acceptance Criteria

1. WHEN a farmer accesses the Dashboard, THE CarbonReady_System SHALL display the current Net_Carbon_Position
2. WHEN a farmer accesses the Dashboard, THE CarbonReady_System SHALL display the current Carbon_Readiness_Index with its classification
3. WHEN a farmer accesses the Dashboard, THE CarbonReady_System SHALL display the Soil_Organic_Carbon trend with visual indicators
4. WHEN a farmer accesses the Dashboard, THE CarbonReady_System SHALL display a breakdown of sequestration versus emissions
5. WHEN a farmer accesses the Dashboard, THE CarbonReady_System SHALL display historical trends for Net_Carbon_Position over the past 12 months
6. WHEN a farmer accesses the Dashboard, THE CarbonReady_System SHALL display the most recent environmental sensor readings
7. WHEN Dashboard data is more than 24 hours old, THE CarbonReady_System SHALL display a staleness indicator

### Requirement 11: Device Authentication and Security

**User Story:** As a system administrator, I want all devices to be securely authenticated, so that unauthorized devices cannot inject false data.

#### Acceptance Criteria

1. WHEN an ESP32_Sensor attempts to connect, THE CarbonReady_System SHALL require X.509 certificate-based authentication
2. IF an ESP32_Sensor fails authentication, THEN THE CarbonReady_System SHALL reject the connection and log the attempt
3. WHEN an ESP32_Sensor is provisioned, THE CarbonReady_System SHALL generate unique device credentials
4. WHEN device credentials are generated, THE CarbonReady_System SHALL store them securely in AWS_IoT_Core device registry
5. WHEN data is transmitted from ESP32_Sensor to AWS_IoT_Core, THE CarbonReady_System SHALL use TLS 1.2 or higher encryption

### Requirement 12: Scalability and Performance

**User Story:** As a system administrator, I want the platform to handle growth from 1 to 100 farms in the pilot phase, so that we can validate the architecture before broader expansion.

#### Acceptance Criteria

1. WHEN the system processes sensor data, THE Data_Ingestion_Pipeline SHALL handle at least 100 messages per second to support 100 farms
2. WHEN the system stores data, THE CarbonReady_System SHALL use DynamoDB with on-demand capacity mode for pilot phase flexibility
3. WHEN the system performs AI calculations, THE AI_Processing_Pipeline SHALL process biomass calculations for 100 farms within 5 minutes
4. WHEN Lambda functions are invoked, THE CarbonReady_System SHALL configure them with appropriate memory and timeout settings to prevent failures
5. WHEN S3 storage is used, THE CarbonReady_System SHALL implement lifecycle policies to archive data older than 1 year to Glacier
6. WHEN the system architecture is designed, THE CarbonReady_System SHALL use serverless and managed services that can scale beyond 100 farms without architectural changes

### Requirement 13: Cost Optimization

**User Story:** As a project manager, I want to keep hardware costs low, so that the solution is affordable for smallholder farmers.

#### Acceptance Criteria

1. WHEN deploying edge devices, THE CarbonReady_System SHALL use ESP32_Sensor hardware with total cost not exceeding ₹3,000 per farm
2. WHEN selecting cloud services, THE CarbonReady_System SHALL use serverless architectures to minimize idle resource costs
3. WHEN storing data, THE CarbonReady_System SHALL compress sensor data before transmission to reduce data transfer costs
4. WHEN processing data, THE AI_Processing_Pipeline SHALL batch calculations to optimize Lambda execution costs

### Requirement 14: Error Handling and Monitoring

**User Story:** As a system administrator, I want to be notified of system errors, so that I can maintain reliable service for farmers.

#### Acceptance Criteria

1. WHEN a Lambda function fails, THE CarbonReady_System SHALL log the error to CloudWatch with full context
2. WHEN sensor data transmission fails, THE ESP32_Sensor SHALL retry transmission up to 3 times with exponential backoff
3. IF sensor data cannot be transmitted after retries, THEN THE ESP32_Sensor SHALL store data locally and transmit when connectivity is restored
4. WHEN critical errors occur, THE CarbonReady_System SHALL send notifications to system administrators via SNS
5. WHEN the Dashboard cannot retrieve data, THE CarbonReady_System SHALL display a user-friendly error message

### Requirement 15: Data Quality and Validation

**User Story:** As a data scientist, I want to ensure data quality, so that AI models produce accurate carbon estimates.

#### Acceptance Criteria

1. WHEN sensor readings are received, THE Data_Ingestion_Pipeline SHALL validate that soil moisture values are between 0% and 100%
2. WHEN sensor readings are received, THE Data_Ingestion_Pipeline SHALL validate that temperature values are between -10°C and 60°C
3. WHEN sensor readings are received, THE Data_Ingestion_Pipeline SHALL validate that humidity values are between 0% and 100%
4. IF sensor readings are outside valid ranges, THEN THE Data_Ingestion_Pipeline SHALL flag the data as anomalous and exclude it from calculations
5. WHEN farm metadata is submitted, THE CarbonReady_System SHALL validate that tree age is between 1 and 100 years
6. WHEN farm metadata is submitted, THE CarbonReady_System SHALL validate that DBH values are between 1 and 200 centimeters
7. WHEN farm metadata is submitted, THE CarbonReady_System SHALL validate that tree height values are between 1 and 40 meters

### Requirement 16: Data Integrity Verification

**User Story:** As a system administrator, I want to verify that sensor data has not been tampered with during transmission, so that I can trust the data used for carbon calculations.

#### Acceptance Criteria

1. WHEN an ESP32_Sensor prepares a data payload, THE ESP32_Sensor SHALL compute a cryptographic hash of the payload using SHA-256
2. WHEN an ESP32_Sensor transmits data, THE ESP32_Sensor SHALL include the cryptographic hash in the message
3. WHEN the Data_Ingestion_Pipeline receives sensor data, THE Data_Ingestion_Pipeline SHALL recompute the cryptographic hash of the payload
4. WHEN the Data_Ingestion_Pipeline verifies data integrity, THE Data_Ingestion_Pipeline SHALL compare the received hash with the computed hash
5. IF the cryptographic hashes do not match, THEN THE Data_Ingestion_Pipeline SHALL reject the data and log a tampering alert
6. WHEN tampered data is detected, THE Data_Ingestion_Pipeline SHALL send a notification to system administrators via SNS
7. WHEN data integrity is verified successfully, THE Data_Ingestion_Pipeline SHALL proceed with normal data storage and processing

### Requirement 17: Carbon Readiness Transparency

**User Story:** As a farmer, I want to understand how my Carbon Readiness Index is calculated, so that I can identify specific areas for improvement.

#### Acceptance Criteria

1. WHEN displaying the Carbon_Readiness_Index, THE Dashboard SHALL provide a breakdown of individual component contributions to the total score
2. WHEN displaying the Carbon_Readiness_Index, THE Dashboard SHALL show the weighting values used in the current calculation
3. WHEN a Carbon_Readiness_Index is calculated, THE AI_Processing_Pipeline SHALL log the version of scoring logic used
4. WHEN a farmer views the Carbon_Readiness_Index breakdown, THE Dashboard SHALL display the score contribution from Net_Carbon_Position
5. WHEN a farmer views the Carbon_Readiness_Index breakdown, THE Dashboard SHALL display the score contribution from Soil_Organic_Carbon trend
6. WHEN a farmer views the Carbon_Readiness_Index breakdown, THE Dashboard SHALL display the score contribution from sustainable management practices

### Requirement 18: Sensor Calibration Management

**User Story:** As a system administrator, I want to track sensor calibration events, so that I can ensure data accuracy over time.

#### Acceptance Criteria

1. WHEN an ESP32_Sensor is installed, THE CarbonReady_System SHALL require sensor calibration confirmation before accepting data
2. WHEN a sensor calibration is performed, THE CarbonReady_System SHALL log the calibration event with timestamp and device ID
3. WHEN a sensor has been in operation, THE CarbonReady_System SHALL support recalibration logging at least once per year
4. WHEN a sensor has not been calibrated for more than 365 days, THE CarbonReady_System SHALL flag the sensor as requiring recalibration
5. WHEN calibration events are stored, THE CarbonReady_System SHALL include calibration parameters and reference values
6. WHEN a sensor is flagged for recalibration, THE Dashboard SHALL display a notification to the system administrator

### Requirement 19: AI Model Versioning and Governance

**User Story:** As a data scientist, I want to track which AI model versions are used for calculations, so that I can ensure reproducibility and manage model updates.

#### Acceptance Criteria

1. WHEN AI models are deployed for biomass calculation, THE AI_Processing_Pipeline SHALL assign a unique version identifier to each model
2. WHEN AI models are deployed for emissions calculation, THE AI_Processing_Pipeline SHALL assign a unique version identifier to each model
3. WHEN a carbon calculation is performed, THE AI_Processing_Pipeline SHALL log the model version associated with the calculation
4. WHEN storing calculation results, THE CarbonReady_System SHALL include the model version identifier in the metadata
5. WHEN a new model version is deployed, THE AI_Processing_Pipeline SHALL maintain previous model versions for rollback capability
6. WHEN a model rollback is requested, THE AI_Processing_Pipeline SHALL allow switching to a previous model version
7. WHEN a model version is changed, THE CarbonReady_System SHALL log the change event with timestamp and reason
8. WHEN carbon calculation metadata is stored, THE CarbonReady_System SHALL retain the metadata and associated model versions for a minimum of 10 years for audit traceability
