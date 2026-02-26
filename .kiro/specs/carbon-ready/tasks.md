# Implementation Plan: CarbonReady

## Overview

This implementation plan breaks down the CarbonReady carbon intelligence platform into discrete coding tasks. The plan follows an incremental approach, building from infrastructure setup through data ingestion, AI processing, and finally the dashboard interface. Each task builds on previous work, with checkpoints to ensure quality and correctness.

## Tasks

- [x] 1. Set up AWS infrastructure and project structure
  - Create AWS CDK project structure with Python
  - Define DynamoDB table schemas (SensorData, FarmMetadata, CarbonCalculations, AIModelRegistry, SensorCalibration, CRIWeights)
  - Define S3 bucket structure with lifecycle policies
  - Set up AWS IoT Core with certificate-based authentication
  - Configure CloudWatch logging and SNS topics
  - _Requirements: 3.1, 3.4, 3.5, 3.6, 11.1, 11.3, 11.4, 11.5, 12.1, 12.2, 12.4, 12.5, 12.6, 14.1, 14.4_

- [x] 2. Implement ESP32 sensor firmware
  - [x] 2.1 Create sensor reading module
    - Implement functions to read soil moisture, soil temperature, air temperature, and humidity
    - Add UTC timestamp generation
    - Ensure readings occur at 15-minute intervals
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ]* 2.2 Write property test for sensor collection intervals
    - **Property 1: Sensor Collection Interval Compliance**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
  
  - [x] 2.3 Implement data payload creation with cryptographic hashing
    - Create JSON payload with sensor readings and farm ID
    - Compute SHA-256 hash of payload
    - Compress data before transmission
    - _Requirements: 1.6, 16.1, 16.2, 13.3_
  
  - [ ]* 2.4 Write property test for cryptographic hash inclusion
    - **Property 37: Cryptographic Hash Inclusion**
    - **Validates: Requirements 16.1, 16.2**
  
  - [x] 2.5 Implement MQTT client with retry logic
    - Connect to AWS IoT Core using X.509 certificates
    - Publish to carbonready/farm/{farmId}/sensor/data topic
    - Implement exponential backoff retry (3 attempts)
    - Store data locally if transmission fails after retries
    - _Requirements: 3.1, 11.5, 14.2, 14.3_
  
  - [ ]* 2.6 Write property test for transmission retry behavior
    - **Property 31: Sensor Transmission Retry Behavior**
    - **Validates: Requirements 14.2**

- [x] 3. Checkpoint - Verify sensor firmware compiles and basic MQTT connectivity works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Data Ingestion Lambda
  - [x] 4.1 Create Lambda function for data ingestion
    - Parse incoming MQTT messages from IoT Core
    - Implement cryptographic hash verification
    - Validate sensor data ranges (soil moisture: 0-100%, temperature: -10°C to 60°C, humidity: 0-100%)
    - Check sensor calibration status
    - Store valid data in DynamoDB and archive to S3
    - Log errors and send SNS notifications for tampering/critical errors
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 15.1, 15.2, 15.3, 15.4, 16.3, 16.4, 16.5, 16.7, 18.1, 18.4_
  
  - [ ]* 4.2 Write property test for data integrity verification
    - **Property 38: Data Integrity Verification**
    - **Validates: Requirements 16.5, 16.7**
  
  - [ ]* 4.3 Write property test for sensor data range validation
    - **Property 35: Sensor Data Range Validation**
    - **Validates: Requirements 15.1, 15.2, 15.3, 15.4**
  
  - [ ]* 4.4 Write unit tests for error handling paths
    - Test malformed data rejection
    - Test hash mismatch handling
    - Test out-of-range value handling
    - Test uncalibrated sensor rejection
    - _Requirements: 3.3, 15.4, 16.5, 18.1_

- [x] 5. Implement Farm Metadata Service
  - [x] 5.1 Create API Lambda for farm metadata management
    - Implement POST /api/v1/farms/{farmId}/metadata endpoint
    - Implement GET /api/v1/farms/{farmId}/metadata endpoint
    - Implement PUT /api/v1/farms/{farmId}/metadata endpoint
    - Validate metadata ranges (tree age: 1-100, DBH: 1-200, height: 1-40, farmSize > 0)
    - Store metadata with versioning in DynamoDB
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 3.6_
  
  - [ ]* 5.2 Write property test for metadata range validation
    - **Property 4: Metadata Range Validation**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**
  
  - [ ]* 5.3 Write property test for metadata versioning
    - **Property 9: Metadata Versioning**
    - **Validates: Requirements 3.6**
  
  - [ ]* 5.4 Write property test for validation error messages
    - **Property 5: Validation Error Message Completeness**
    - **Validates: Requirements 2.8**

- [ ] 6. Checkpoint - Verify data ingestion and metadata APIs work end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement biomass calculation module
  - [ ] 7.1 Create allometric equation functions
    - Implement calculate_cashew_biomass(dbh, age) using DBH and age
    - Implement calculate_coconut_biomass(height, age) using height and age
    - Implement calculate_farm_biomass(metadata) that multiplies per-tree biomass by density and farm size
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ] 7.2 Write property test for crop-specific biomass calculation
    - **Property 10: Crop-Specific Biomass Calculation**
    - **Validates: Requirements 4.1, 4.2**
  
  - [ ] 7.3 Write property test for farm biomass scaling
    - **Property 11: Farm Biomass Scaling**
    - **Validates: Requirements 4.3**
  
  - [ ] 7.4 Implement carbon stock and CO₂ equivalent conversion
    - Create convert_biomass_to_co2e(biomass_kg) function (biomass × 0.5 × 3.667)
    - This is the central conversion function used throughout the system
    - Store results with 2 decimal precision
    - _Requirements: 5.1, 5.2, 5.3, 4.4_
  
  - [ ] 7.5 Write property test for carbon stock calculation
    - **Property 13: Carbon Stock Calculation Accuracy**
    - **Validates: Requirements 5.1**
  
  - [ ] 7.6 Write property test for CO₂ equivalent conversion
    - **Property 14: CO₂ Equivalent Conversion Accuracy**
    - **Validates: Requirements 5.2**
  
  - [ ]* 7.7 Write property test for numeric precision
    - **Property 12: Numeric Precision Consistency**
    - **Validates: Requirements 4.4, 5.3, 7.4**

- [ ] 8. Implement annual sequestration module
  - [ ] 8.1 Create growth curve estimation function
    - Implement estimate_sequestration_from_growth_curves(tree_age, crop_type, region)
    - Load regional growth curve parameters from DynamoDB
    - Return biomass increment in kg (NOT CO₂e)
    - _Requirements: 8.1, 8.2_
  
  - [ ] 8.2 Implement sequestration calculation logic
    - Calculate biomass increment from historical data when available
    - Use growth curves as fallback when historical data unavailable
    - Convert to CO₂e using central convert_biomass_to_co2e() function
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ]* 8.3 Write property test for sequestration calculation method selection
    - **Property 20: Sequestration Calculation Method Selection**
    - **Validates: Requirements 8.1, 8.2**
  
  - [ ]* 8.4 Write property test for sequestration unit consistency
    - **Property 21: Sequestration Unit Consistency**
    - **Validates: Requirements 8.3**

- [ ] 9. Implement emissions calculation module
  - [ ] 9.1 Create emissions calculation function
    - Implement calculate_emissions(metadata) using IPCC Tier 1 factors
    - Calculate fertilizer emissions: total_fertilizer = fertilizerUsage × farmSizeHectares, then apply 0.01 factor
    - Calculate irrigation emissions: total_irrigation = irrigationActivity × farmSizeHectares, then apply energy factor
    - Return emissions in CO₂e kg/year with 2 decimal precision
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [ ] 9.2 Write property test for IPCC emission factor usage
    - **Property 18: IPCC Emission Factor Usage**
    - **Validates: Requirements 7.1, 7.2**
  
  - [ ]* 9.3 Write property test for emissions unit consistency
    - **Property 19: Emissions Unit Consistency**
    - **Validates: Requirements 7.3**

- [ ]* 10. Implement SOC trend analysis module
  - [ ]* 10.1 Create SOC proxy model function
    - Implement calculate_soc_proxy_model() with weighted multi-factor equation
    - Use weights: biomass_return (40%), management (30%), temperature (15%), moisture (15%)
    - Return normalized score between -1 and +1
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [ ]* 10.2 Implement SOC trend analysis function
    - Implement analyze_soc_trend(farm_id, metadata)
    - Check for minimum 90 days of data
    - Calculate biomass return, management score, environmental context
    - Apply SOC proxy model
    - Classify as "Improving" (> 0.05), "Stable" (-0.05 to 0.05), or "Declining" (< -0.05)
    - _Requirements: 6.1, 6.5, 6.6, 6.7_
  
  - [ ]* 10.3 Write property test for SOC data sufficiency requirement
    - **Property 16: SOC Data Sufficiency Requirement**
    - **Validates: Requirements 6.5, 6.6**
  
  - [ ]* 10.4 Write property test for SOC classification validity
    - **Property 17: SOC Classification Validity**
    - **Validates: Requirements 6.7**
  
  - [ ]* 10.5 Write property test for SOC model input completeness
    - **Property 15: SOC Model Input Completeness**
    - **Validates: Requirements 6.1**

- [ ] 11. Checkpoint - Verify all calculation modules produce correct outputs
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement net carbon position calculation
  - [ ] 12.1 Create net carbon position function
    - Calculate net_position = annual_sequestration_co2e - annual_emissions_co2e
    - Classify as "Net Carbon Sink" (positive) or "Net Carbon Source" (negative)
    - Store in CO₂e kg/year
    - _Requirements: 8.4, 8.5, 8.6, 8.7_
  
  - [ ] 12.2 Write property test for net carbon position calculation
    - **Property 22: Net Carbon Position Calculation Accuracy**
    - **Validates: Requirements 8.4**
  
  - [ ] 12.3 Write property test for net carbon classification
    - **Property 23: Net Carbon Classification Logic**
    - **Validates: Requirements 8.5, 8.6**

- [ ] 13. Implement Carbon Readiness Index module
  - [ ]* 13.1 Create CRI weight management functions
    - Implement get_cri_weights() to retrieve weights from DynamoDB
    - Implement set_cri_weights() with admin authorization check
    - Validate weights sum to 1.0 (with 0.001 tolerance)
    - Use default weights (50%, 30%, 20%) if not specified
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [ ]* 13.2 Write property test for CRI weight validation
    - **Property 25: CRI Weight Validation and Default Fallback**
    - **Validates: Requirements 9.2, 9.3, 9.4**
  
  - [ ]* 13.3 Write property test for CRI weight modification authorization
    - **Property 26: CRI Weight Modification Authorization**
    - **Validates: Requirements 9.5, 9.6**
  
  - [ ] 13.4 Implement net position normalization function
    - Create normalize_net_position(net_position, farm_size_hectares)
    - Normalize to per-hectare basis
    - Map -1000 to +1000 kg CO₂e/ha/year to 0-100 score
    - _Requirements: 9.1_
  
  - [ ] 13.5 Implement CRI calculation function
    - Create calculate_carbon_readiness_index(net_position, soc_trend, management_practices, weights)
    - Calculate weighted sum of normalized components
    - Normalize final score to 0-100
    - Classify as "Needs Improvement" (< 40), "Moderate" (40-70), or "Excellent" (> 70)
    - _Requirements: 9.1, 9.7, 9.8, 9.9, 9.10_
  
  - [ ] 13.6 Write property test for CRI component completeness
    - **Property 24: CRI Component Completeness**
    - **Validates: Requirements 9.1**
  
  - [ ]* 13.7 Write property test for CRI score normalization
    - **Property 27: CRI Score Normalization**
    - **Validates: Requirements 9.7**
  
  - [ ] 13.8 Write property test for CRI classification thresholds
    - **Property 28: CRI Classification Thresholds**
    - **Validates: Requirements 9.8, 9.9, 9.10**

- [ ] 14. Implement AI Processing Pipeline Lambda
  - [ ] 14.1 Create main carbon calculation orchestration function
    - Implement process_farm_carbon(farm_id) that orchestrates all calculations
    - Retrieve farm metadata and historical biomass data
    - Calculate biomass, sequestration, emissions, SOC trend, net position, and CRI
    - Store results with model version metadata in DynamoDB
    - Set retention timestamp to +10 years
    - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 6.1, 7.1, 8.1, 8.4, 9.1, 19.3, 19.4, 19.8_
  
  - [ ] 14.2 Implement EventBridge scheduled trigger
    - Configure daily trigger at 02:00 UTC
    - Batch process all farms (up to 100 in pilot)
    - _Requirements: 12.3_
  
  - [ ]* 14.3 Write integration test for complete carbon calculation workflow
    - Test end-to-end calculation with sample farm data
    - Verify all components are calculated and stored
    - _Requirements: 4.1, 5.1, 6.1, 7.1, 8.1, 9.1_

- [ ]* 15. Implement AI model versioning service
  - [ ]* 15.1 Create model registry functions
    - Implement register_model(model_type, version, parameters) to store in DynamoDB
    - Implement get_active_model_version(model_type) to retrieve current version
    - Implement rollback_model(model_type, target_version) to switch versions
    - Log all model version changes with timestamp and reason
    - Set retention to +10 years
    - _Requirements: 19.1, 19.2, 19.5, 19.6, 19.7, 19.8_
  
  - [ ]* 15.2 Write property test for model version assignment
    - **Property 43: AI Model Version Assignment**
    - **Validates: Requirements 19.1, 19.2**
  
  - [ ]* 15.3 Write property test for calculation model version logging
    - **Property 44: Calculation Model Version Logging**
    - **Validates: Requirements 19.3, 19.4**
  
  - [ ]* 15.4 Write property test for model version retention
    - **Property 45: Model Version Retention**
    - **Validates: Requirements 19.5**
  
  - [ ]* 15.5 Write property test for model rollback capability
    - **Property 46: Model Rollback Capability**
    - **Validates: Requirements 19.6**

- [ ] 16. Checkpoint - Verify AI processing pipeline runs successfully
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 17. Implement sensor calibration service
  - [ ]* 17.1 Create calibration management functions
    - Implement log_calibration(device_id, calibration_params) to store in DynamoDB
    - Implement check_calibration_status(device_id) to verify calibration validity
    - Flag sensors with calibration > 365 days old
    - _Requirements: 18.1, 18.2, 18.4, 18.5_
  
  - [ ]* 17.2 Write property test for uncalibrated sensor rejection
    - **Property 40: Uncalibrated Sensor Rejection**
    - **Validates: Requirements 18.1**
  
  - [ ]* 17.3 Write property test for calibration event logging
    - **Property 41: Calibration Event Logging**
    - **Validates: Requirements 18.2, 18.5**
  
  - [ ]* 17.4 Write property test for calibration expiry flagging
    - **Property 42: Calibration Expiry Flagging**
    - **Validates: Requirements 18.4, 18.6**

- [ ] 18. Implement Dashboard API Lambda
  - [ ] 18.1 Create API endpoints for carbon intelligence data
    - Implement GET /api/v1/farms/{farmId}/carbon-position
    - Implement GET /api/v1/farms/{farmId}/carbon-readiness-index with full breakdown
    - Implement GET /api/v1/farms/{farmId}/sensor-data/latest
    - Implement GET /api/v1/farms/{farmId}/historical-trends?days=365
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 17.1, 17.2, 17.3_
  
  - [ ] 18.2 Implement authentication and authorization
    - Set up Amazon Cognito user pools
    - Implement JWT token validation
    - Implement basic role-based access control (farmer role)
    - _Requirements: 9.5, 9.6_
  
  - [ ]* 18.3 Write property test for dashboard API data completeness
    - **Property 29: Dashboard API Data Completeness**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6**
  
  - [ ]* 18.4 Write property test for CRI transparency and breakdown
    - **Property 39: CRI Transparency and Breakdown**
    - **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6**
  
  - [ ]* 18.5 Write unit tests for API error handling
    - Test user-friendly error messages
    - Test authorization failures
    - _Requirements: 14.5_

- [ ]* 19. Implement error handling and monitoring
  - [ ]* 19.1 Add CloudWatch logging to all Lambda functions
    - Log all errors with full context
    - Log authentication failures
    - Log data validation errors
    - _Requirements: 14.1_
  
  - [ ]* 19.2 Configure SNS notifications
    - Set up carbonready-critical-alerts topic
    - Set up carbonready-warnings topic
    - Send notifications for Lambda failures, data tampering, calibration expiry
    - _Requirements: 14.4, 16.6, 18.6_
  
  - [ ]* 19.3 Write property test for Lambda error logging
    - **Property 30: Lambda Error Logging**
    - **Validates: Requirements 14.1**
  
  - [ ]* 19.4 Write property test for critical error notification
    - **Property 33: Critical Error Notification**
    - **Validates: Requirements 14.4, 16.6**

- [ ] 20. Implement web dashboard frontend
  - [ ] 20.1 Create dashboard UI components
    - Display net carbon position with classification
    - Display Carbon Readiness Index with score, classification, and component breakdown
    - Display SOC trend with visual indicators
    - Display emissions vs sequestration breakdown
    - Display historical trends chart (12 months)
    - Display latest sensor readings
    - Show staleness indicator for data > 24 hours old
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_
  
  - [ ] 20.2 Implement minimal admin panel
    - Create basic UI for viewing current CRI weights
    - _Requirements: 17.1, 17.2_

- [ ] 21. Final checkpoint - End-to-end system testing
  - Deploy complete system to dev environment
  - Test sensor → cloud → dashboard flow
  - Verify all property tests pass
  - Verify all unit tests pass
  - Run integration tests
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 22. Deploy to production
  - [ ] 22.1 Deploy infrastructure using AWS CDK
    - Deploy to production AWS account
    - Configure production CloudWatch alarms
    - Set up production SNS notifications
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_
  
  - [ ] 22.2 Provision ESP32 devices with certificates
    - Generate unique X.509 certificates for each device
    - Flash firmware to ESP32 devices
    - Store certificates in SPIFFS partition
    - Perform initial sensor calibration
    - _Requirements: 11.1, 11.3, 18.1_
  
  - [ ] 22.3 Onboard pilot farm
    - Create farm metadata entry
    - Deploy ESP32 sensor on farm
    - Verify data ingestion
    - Verify carbon calculations
    - Verify dashboard displays data correctly

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- The implementation uses Python for all Lambda functions and AWS CDK
- ESP32 firmware uses C++ with Arduino framework
- Dashboard frontend can use React/TypeScript or similar modern framework
- All property tests should be tagged with: `# Feature: carbon-ready, Property {number}: {property_text}`
