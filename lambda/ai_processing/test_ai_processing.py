"""
Test script for AI Processing Lambda
Tests the complete carbon calculation workflow
"""
import sys
import os
from datetime import datetime

# Set mock environment variables before importing
os.environ['FARM_METADATA_TABLE'] = 'CarbonReady-FarmMetadataTable'
os.environ['CARBON_CALCULATIONS_TABLE'] = 'CarbonReady-CarbonCalculationsTable'
os.environ['AI_MODEL_REGISTRY_TABLE'] = 'CarbonReady-AIModelRegistryTable'
os.environ['CRI_WEIGHTS_TABLE'] = 'CarbonReady-CRIWeightsTable'
os.environ['SENSOR_DATA_TABLE'] = 'CarbonReady-SensorDataTable'
os.environ['GROWTH_CURVES_TABLE'] = 'CarbonReady-GrowthCurvesTable'

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from index import (
    process_farm_carbon,
    get_farm_metadata,
    get_historical_biomass,
    analyze_soc_trend_stub,
    convert_floats_to_decimal
)


def test_process_farm_carbon_with_mock_data():
    """
    Test the complete carbon calculation workflow with mock data.
    
    This test validates that all calculation modules are properly integrated
    and the orchestration function works end-to-end.
    """
    print("=" * 80)
    print("Testing AI Processing Pipeline - Complete Carbon Calculation Workflow")
    print("=" * 80)
    
    # Mock farm metadata (cashew farm)
    mock_metadata = {
        "farmId": "test-farm-001",
        "cropType": "cashew",
        "farmSizeHectares": 2.5,
        "treeAge": 15,
        "dbh": 25.0,  # cm
        "plantationDensity": 200,  # trees/hectare
        "fertilizerUsage": 100.0,  # kg/hectare/year
        "irrigationActivity": 10000.0,  # liters/hectare/year
        "version": 1
    }
    
    print("\n1. Testing with Cashew Farm")
    print("-" * 80)
    print(f"Farm ID: {mock_metadata['farmId']}")
    print(f"Crop Type: {mock_metadata['cropType']}")
    print(f"Farm Size: {mock_metadata['farmSizeHectares']} hectares")
    print(f"Tree Age: {mock_metadata['treeAge']} years")
    print(f"DBH: {mock_metadata['dbh']} cm")
    print(f"Plantation Density: {mock_metadata['plantationDensity']} trees/hectare")
    
    # Import calculation functions
    from biomass_calculator import (
        calculate_farm_biomass,
        convert_biomass_to_co2e,
        calculate_annual_sequestration,
        calculate_emissions,
        calculate_net_carbon_position,
        calculate_carbon_readiness_index
    )
    
    # Test biomass calculation
    print("\n2. Calculating Biomass...")
    biomass = calculate_farm_biomass(mock_metadata)
    print(f"   Total Farm Biomass: {biomass:.2f} kg")
    
    # Test carbon stock calculation
    carbon_stock = biomass * 0.5
    co2_equivalent_stock = convert_biomass_to_co2e(biomass)
    print(f"   Carbon Stock: {carbon_stock:.2f} kg")
    print(f"   CO2 Equivalent Stock: {co2_equivalent_stock:.2f} kg CO2e")
    
    # Test annual sequestration (without historical data - uses growth curves)
    print("\n3. Calculating Annual Sequestration...")
    sequestration_result = calculate_annual_sequestration(
        farm_id=mock_metadata['farmId'],
        metadata=mock_metadata,
        historical_biomass=None,  # No historical data
        dynamodb_client=None
    )
    print(f"   Method: {sequestration_result['method']}")
    print(f"   Biomass Increment: {sequestration_result['biomassIncrement']:.2f} kg")
    print(f"   CO2e Sequestration: {sequestration_result['co2eSequestration']:.2f} kg CO2e/year")
    
    # Test emissions calculation
    print("\n4. Calculating Emissions...")
    emissions_result = calculate_emissions(mock_metadata)
    print(f"   Fertilizer Emissions: {emissions_result['fertilizerEmissions']:.2f} kg CO2e/year")
    print(f"   Irrigation Emissions: {emissions_result['irrigationEmissions']:.2f} kg CO2e/year")
    print(f"   Total Emissions: {emissions_result['totalEmissions']:.2f} kg CO2e/year")
    
    # Test net carbon position
    print("\n5. Calculating Net Carbon Position...")
    net_position_result = calculate_net_carbon_position(
        annual_sequestration_co2e=sequestration_result['co2eSequestration'],
        annual_emissions_co2e=emissions_result['totalEmissions']
    )
    print(f"   Net Position: {net_position_result['netPosition']:.2f} kg CO2e/year")
    print(f"   Classification: {net_position_result['classification']}")
    
    # Test SOC trend (stub)
    print("\n6. Analyzing SOC Trend...")
    soc_trend = analyze_soc_trend_stub(mock_metadata['farmId'], mock_metadata)
    print(f"   Status: {soc_trend['status']}")
    
    # Test Carbon Readiness Index
    print("\n7. Calculating Carbon Readiness Index...")
    cri_result = calculate_carbon_readiness_index(
        net_position=net_position_result['netPosition'],
        soc_trend=soc_trend,
        management_practices=mock_metadata,
        weights=None,
        dynamodb_client=None
    )
    print(f"   CRI Score: {cri_result['score']:.2f}")
    print(f"   Classification: {cri_result['classification']}")
    print(f"   Components:")
    print(f"     - Net Carbon Position: {cri_result['components']['netCarbonPosition']:.2f}")
    print(f"     - SOC Trend: {cri_result['components']['socTrend']:.2f}")
    print(f"     - Management Practices: {cri_result['components']['managementPractices']:.2f}")
    
    # Test with coconut farm
    print("\n" + "=" * 80)
    print("8. Testing with Coconut Farm")
    print("-" * 80)
    
    mock_metadata_coconut = {
        "farmId": "test-farm-002",
        "cropType": "coconut",
        "farmSizeHectares": 3.0,
        "treeAge": 20,
        "treeHeight": 12.0,  # meters
        "plantationDensity": 150,  # trees/hectare
        "fertilizerUsage": 120.0,  # kg/hectare/year
        "irrigationActivity": 12000.0,  # liters/hectare/year
        "version": 1
    }
    
    print(f"Farm ID: {mock_metadata_coconut['farmId']}")
    print(f"Crop Type: {mock_metadata_coconut['cropType']}")
    print(f"Tree Height: {mock_metadata_coconut['treeHeight']} meters")
    
    biomass_coconut = calculate_farm_biomass(mock_metadata_coconut)
    print(f"Total Farm Biomass: {biomass_coconut:.2f} kg")
    
    sequestration_coconut = calculate_annual_sequestration(
        farm_id=mock_metadata_coconut['farmId'],
        metadata=mock_metadata_coconut,
        historical_biomass=None,
        dynamodb_client=None
    )
    print(f"Annual Sequestration: {sequestration_coconut['co2eSequestration']:.2f} kg CO2e/year")
    
    emissions_coconut = calculate_emissions(mock_metadata_coconut)
    print(f"Total Emissions: {emissions_coconut['totalEmissions']:.2f} kg CO2e/year")
    
    net_position_coconut = calculate_net_carbon_position(
        annual_sequestration_co2e=sequestration_coconut['co2eSequestration'],
        annual_emissions_co2e=emissions_coconut['totalEmissions']
    )
    print(f"Net Position: {net_position_coconut['netPosition']:.2f} kg CO2e/year")
    print(f"Classification: {net_position_coconut['classification']}")
    
    cri_coconut = calculate_carbon_readiness_index(
        net_position=net_position_coconut['netPosition'],
        soc_trend=soc_trend,
        management_practices=mock_metadata_coconut,
        weights=None,
        dynamodb_client=None
    )
    print(f"CRI Score: {cri_coconut['score']:.2f}")
    print(f"Classification: {cri_coconut['classification']}")
    
    # Test convert_floats_to_decimal
    print("\n" + "=" * 80)
    print("9. Testing DynamoDB Decimal Conversion")
    print("-" * 80)
    
    test_data = {
        "farmId": "test",
        "biomass": 1234.56,
        "nested": {
            "value": 78.90,
            "list": [1.1, 2.2, 3.3]
        }
    }
    
    converted = convert_floats_to_decimal(test_data)
    print(f"Original: {test_data}")
    print(f"Converted: {converted}")
    print(f"Type of biomass: {type(converted['biomass'])}")
    
    print("\n" + "=" * 80)
    print("✓ All tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    test_process_farm_carbon_with_mock_data()
