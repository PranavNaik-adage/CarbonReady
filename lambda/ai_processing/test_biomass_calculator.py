"""
Unit tests for biomass_calculator module
"""
import pytest
import biomass_calculator as bc
from biomass_calculator import (
    calculate_cashew_biomass,
    calculate_coconut_biomass,
    calculate_farm_biomass,
    convert_biomass_to_co2e
)


class TestCashewBiomass:
    """Test cashew biomass calculation"""
    
    def test_basic_calculation(self):
        """Test basic cashew biomass calculation with typical values"""
        dbh = 20.0  # cm
        age = 10  # years
        biomass = calculate_cashew_biomass(dbh, age)
        
        # Expected: 0.28 * (20^2.15) * (1 + 0.02*10)
        # = 0.28 * 175.55 * 1.2 ≈ 210.6 kg
        assert biomass > 0
        assert 200 < biomass < 220
    
    def test_young_tree(self):
        """Test biomass for young cashew tree"""
        dbh = 5.0  # cm
        age = 3  # years
        biomass = calculate_cashew_biomass(dbh, age)
        
        assert biomass > 0
        assert biomass < 10  # Young tree should have low biomass
    
    def test_mature_tree(self):
        """Test biomass for mature cashew tree"""
        dbh = 50.0  # cm
        age = 30  # years
        biomass = calculate_cashew_biomass(dbh, age)
        
        assert biomass > 500  # Mature tree should have high biomass


class TestCoconutBiomass:
    """Test coconut biomass calculation"""
    
    def test_basic_calculation(self):
        """Test basic coconut biomass calculation with typical values"""
        height = 10.0  # meters
        age = 15  # years
        biomass = calculate_coconut_biomass(height, age)
        
        # Expected: 15.3 * (10^1.85) * (1 + 0.015*15)
        # = 15.3 * 70.8 * 1.225 ≈ 1327 kg
        assert biomass > 0
        assert 1200 < biomass < 1500
    
    def test_young_tree(self):
        """Test biomass for young coconut tree"""
        height = 3.0  # meters
        age = 5  # years
        biomass = calculate_coconut_biomass(height, age)
        
        assert biomass > 0
        assert biomass < 200  # Young tree should have low biomass
    
    def test_mature_tree(self):
        """Test biomass for mature coconut tree"""
        height = 20.0  # meters
        age = 40  # years
        biomass = calculate_coconut_biomass(height, age)
        
        assert biomass > 2000  # Mature tree should have high biomass


class TestFarmBiomass:
    """Test farm-level biomass calculation"""
    
    def test_cashew_farm(self):
        """Test total biomass for cashew farm"""
        metadata = {
            "cropType": "cashew",
            "treeAge": 10,
            "dbh": 20.0,
            "plantationDensity": 200,  # trees/hectare
            "farmSizeHectares": 2.0
        }
        
        total_biomass = calculate_farm_biomass(metadata)
        
        # Per-tree biomass ≈ 210.6 kg
        # Total trees = 200 * 2 = 400
        # Total biomass ≈ 210.6 * 400 = 84,240 kg
        assert total_biomass > 80000
        assert total_biomass < 90000
    
    def test_coconut_farm(self):
        """Test total biomass for coconut farm"""
        metadata = {
            "cropType": "coconut",
            "treeAge": 15,
            "treeHeight": 10.0,
            "plantationDensity": 150,  # trees/hectare
            "farmSizeHectares": 1.5
        }
        
        total_biomass = calculate_farm_biomass(metadata)
        
        # Per-tree biomass ≈ 1327 kg
        # Total trees = 150 * 1.5 = 225
        # Total biomass ≈ 1327 * 225 = 298,575 kg
        assert total_biomass > 280000
        assert total_biomass < 320000
    
    def test_invalid_crop_type(self):
        """Test that invalid crop type raises error"""
        metadata = {
            "cropType": "mango",
            "treeAge": 10,
            "plantationDensity": 200,
            "farmSizeHectares": 2.0
        }
        
        with pytest.raises(ValueError, match="Unsupported crop type"):
            calculate_farm_biomass(metadata)


class TestCO2Conversion:
    """Test CO₂ equivalent conversion"""
    
    def test_basic_conversion(self):
        """Test basic biomass to CO₂e conversion"""
        biomass = 1000.0  # kg
        co2e = convert_biomass_to_co2e(biomass)
        
        # Expected: 1000 * 0.5 * 3.667 = 1833.5 kg CO₂e
        assert co2e == 1833.5
    
    def test_precision(self):
        """Test that result is rounded to 2 decimal places"""
        biomass = 123.456  # kg
        co2e = convert_biomass_to_co2e(biomass)
        
        # Expected: 123.456 * 0.5 * 3.667 = 226.36 kg CO₂e
        assert co2e == 226.36
        
        # Verify it's rounded to 2 decimals
        assert len(str(co2e).split('.')[-1]) <= 2
    
    def test_zero_biomass(self):
        """Test conversion with zero biomass"""
        biomass = 0.0
        co2e = convert_biomass_to_co2e(biomass)
        
        assert co2e == 0.0
    
    def test_small_biomass(self):
        """Test conversion with small biomass value"""
        biomass = 1.0  # kg
        co2e = convert_biomass_to_co2e(biomass)
        
        # Expected: 1.0 * 0.5 * 3.667 = 1.83 kg CO₂e
        assert co2e == 1.83



class TestGrowthCurves:
    """Test growth curve functions"""
    
    def test_get_default_growth_parameters_cashew(self):
        """Test default growth parameters for cashew"""
        from biomass_calculator import get_default_growth_parameters
        
        params = get_default_growth_parameters('cashew')
        
        assert 'a' in params
        assert 'b' in params
        assert 'c' in params
        assert params['a'] == 250.0
        assert params['b'] == 0.08
        assert params['c'] == 1.5
    
    def test_get_default_growth_parameters_coconut(self):
        """Test default growth parameters for coconut"""
        from biomass_calculator import get_default_growth_parameters
        
        params = get_default_growth_parameters('coconut')
        
        assert 'a' in params
        assert 'b' in params
        assert 'c' in params
        assert params['a'] == 350.0
        assert params['b'] == 0.06
        assert params['c'] == 1.8
    
    def test_get_default_growth_parameters_invalid(self):
        """Test that invalid crop type raises error"""
        from biomass_calculator import get_default_growth_parameters
        
        with pytest.raises(ValueError, match="Unsupported crop type"):
            get_default_growth_parameters('mango')
    
    def test_chapman_richards_biomass(self):
        """Test Chapman-Richards biomass calculation"""
        from biomass_calculator import calculate_chapman_richards_biomass
        
        parameters = {
            'a': 250.0,
            'b': 0.08,
            'c': 1.5
        }
        
        # Test at age 10
        biomass = calculate_chapman_richards_biomass(10, parameters)
        assert biomass > 0
        assert biomass < 250.0  # Should be less than asymptote
        
        # Test at age 50 (should be closer to asymptote)
        biomass_mature = calculate_chapman_richards_biomass(50, parameters)
        assert biomass_mature > biomass
        assert biomass_mature < 250.0
    
    def test_chapman_richards_zero_age(self):
        """Test Chapman-Richards with zero age"""
        from biomass_calculator import calculate_chapman_richards_biomass
        
        parameters = {'a': 250.0, 'b': 0.08, 'c': 1.5}
        biomass = calculate_chapman_richards_biomass(0, parameters)
        
        assert biomass == 0.0
    
    def test_estimate_sequestration_from_growth_curves(self):
        """Test sequestration estimation using growth curves"""
        from biomass_calculator import estimate_sequestration_from_growth_curves
        
        # Test with cashew at age 10
        increment = estimate_sequestration_from_growth_curves(
            tree_age=10,
            crop_type='cashew',
            region='Goa',
            dynamodb_client=None  # Will use defaults
        )
        
        # Should return positive increment
        assert increment > 0
        # Increment should be reasonable (not too large)
        assert increment < 50  # Per-tree increment should be < 50 kg/year
    
    def test_estimate_sequestration_young_tree(self):
        """Test sequestration for young tree (higher growth rate)"""
        from biomass_calculator import estimate_sequestration_from_growth_curves
        
        increment_young = estimate_sequestration_from_growth_curves(
            tree_age=5,
            crop_type='cashew',
            region='Goa',
            dynamodb_client=None
        )
        
        increment_old = estimate_sequestration_from_growth_curves(
            tree_age=50,
            crop_type='cashew',
            region='Goa',
            dynamodb_client=None
        )
        
        # Young trees should have higher growth rate
        assert increment_young > increment_old


class TestAnnualSequestration:
    """Test annual sequestration calculation"""
    
    def test_sequestration_with_historical_data(self):
        """Test sequestration calculation using historical biomass"""
        from biomass_calculator import calculate_annual_sequestration
        
        metadata = {
            "cropType": "cashew",
            "treeAge": 10,
            "dbh": 20.0,
            "plantationDensity": 200,
            "farmSizeHectares": 2.0
        }
        
        # Current biomass ≈ 84,240 kg
        # Historical biomass (1 year ago)
        historical_biomass = 80000.0  # kg
        
        result = calculate_annual_sequestration(
            farm_id="farm-001",
            metadata=metadata,
            historical_biomass=historical_biomass,
            dynamodb_client=None
        )
        
        assert result['method'] == 'historical'
        assert result['biomassIncrement'] > 0
        assert result['co2eSequestration'] > 0
        assert result['unit'] == 'kg CO2e/year'
        
        # Biomass increment ≈ 84240 - 80000 = 4240 kg
        assert 4000 < result['biomassIncrement'] < 5000
        
        # CO2e ≈ 4240 * 0.5 * 3.667 ≈ 7774 kg CO2e
        assert 7000 < result['co2eSequestration'] < 8500
    
    def test_sequestration_without_historical_data(self):
        """Test sequestration calculation using growth curves"""
        from biomass_calculator import calculate_annual_sequestration
        
        metadata = {
            "cropType": "coconut",
            "treeAge": 15,
            "treeHeight": 10.0,
            "plantationDensity": 150,
            "farmSizeHectares": 1.5
        }
        
        result = calculate_annual_sequestration(
            farm_id="farm-002",
            metadata=metadata,
            historical_biomass=None,  # No historical data
            dynamodb_client=None
        )
        
        assert result['method'] == 'growth_curve'
        assert result['biomassIncrement'] >= 0
        assert result['co2eSequestration'] >= 0
        assert result['unit'] == 'kg CO2e/year'
    
    def test_sequestration_negative_increment_handling(self):
        """Test that negative increments are handled (set to zero)"""
        from biomass_calculator import calculate_annual_sequestration
        
        metadata = {
            "cropType": "cashew",
            "treeAge": 10,
            "dbh": 20.0,
            "plantationDensity": 200,
            "farmSizeHectares": 2.0
        }
        
        # Historical biomass higher than current (shouldn't happen, but test handling)
        historical_biomass = 100000.0  # kg (higher than current)
        
        result = calculate_annual_sequestration(
            farm_id="farm-003",
            metadata=metadata,
            historical_biomass=historical_biomass,
            dynamodb_client=None
        )
        
        # Should handle gracefully and return 0
        assert result['biomassIncrement'] == 0
        assert result['co2eSequestration'] == 0.0
    
    def test_sequestration_result_structure(self):
        """Test that result has correct structure"""
        from biomass_calculator import calculate_annual_sequestration
        
        metadata = {
            "cropType": "cashew",
            "treeAge": 10,
            "dbh": 20.0,
            "plantationDensity": 200,
            "farmSizeHectares": 2.0
        }
        
        result = calculate_annual_sequestration(
            farm_id="farm-004",
            metadata=metadata,
            historical_biomass=None,
            dynamodb_client=None
        )
        
        # Verify all required keys are present
        assert 'biomassIncrement' in result
        assert 'co2eSequestration' in result
        assert 'method' in result
        assert 'unit' in result
        
        # Verify types
        assert isinstance(result['biomassIncrement'], (int, float))
        assert isinstance(result['co2eSequestration'], (int, float))
        assert isinstance(result['method'], str)
        assert isinstance(result['unit'], str)



class TestEmissionsCalculation:
    """Test emissions calculation module"""
    
    def test_basic_emissions_calculation(self):
        """Test basic emissions calculation with typical values"""
        from biomass_calculator import calculate_emissions
        
        metadata = {
            "fertilizerUsage": 100.0,  # kg/hectare/year
            "irrigationActivity": 50000.0,  # liters/hectare/year
            "farmSizeHectares": 2.0
        }
        
        result = calculate_emissions(metadata)
        
        # Verify structure
        assert 'fertilizerEmissions' in result
        assert 'irrigationEmissions' in result
        assert 'totalEmissions' in result
        assert 'unit' in result
        assert result['unit'] == 'kg CO2e/year'
        
        # Verify all values are positive
        assert result['fertilizerEmissions'] > 0
        assert result['irrigationEmissions'] > 0
        assert result['totalEmissions'] > 0
        
        # Verify total is sum of components
        assert result['totalEmissions'] == result['fertilizerEmissions'] + result['irrigationEmissions']
    
    def test_fertilizer_emissions_calculation(self):
        """Test fertilizer emissions calculation with known values"""
        from biomass_calculator import calculate_emissions
        
        metadata = {
            "fertilizerUsage": 100.0,  # kg/hectare/year
            "irrigationActivity": 0.0,  # No irrigation
            "farmSizeHectares": 2.0
        }
        
        result = calculate_emissions(metadata)
        
        # Manual calculation:
        # Total fertilizer = 100 * 2 = 200 kg
        # Nitrogen applied = 200 * 0.46 = 92 kg N
        # N2O-N emissions = 92 * 0.01 = 0.92 kg N2O-N
        # N2O emissions = 0.92 * (44/28) = 1.4457 kg N2O
        # CO2e = 1.4457 * 298 = 430.82 kg CO2e
        
        expected_fertilizer_co2e = 430.82
        assert abs(result['fertilizerEmissions'] - expected_fertilizer_co2e) < 0.1
        assert result['irrigationEmissions'] == 0.0
        assert result['totalEmissions'] == result['fertilizerEmissions']
    
    def test_irrigation_emissions_calculation(self):
        """Test irrigation emissions calculation with known values"""
        from biomass_calculator import calculate_emissions
        
        metadata = {
            "fertilizerUsage": 0.0,  # No fertilizer
            "irrigationActivity": 50000.0,  # liters/hectare/year
            "farmSizeHectares": 2.0
        }
        
        result = calculate_emissions(metadata)
        
        # Manual calculation:
        # Total irrigation = 50000 * 2 = 100,000 liters
        # CO2e = (100000 / 1000) * 0.5 = 100 * 0.5 = 50 kg CO2e
        
        expected_irrigation_co2e = 50.0
        assert result['irrigationEmissions'] == expected_irrigation_co2e
        assert result['fertilizerEmissions'] == 0.0
        assert result['totalEmissions'] == result['irrigationEmissions']
    
    def test_combined_emissions(self):
        """Test combined fertilizer and irrigation emissions"""
        from biomass_calculator import calculate_emissions
        
        metadata = {
            "fertilizerUsage": 50.0,  # kg/hectare/year
            "irrigationActivity": 30000.0,  # liters/hectare/year
            "farmSizeHectares": 1.5
        }
        
        result = calculate_emissions(metadata)
        
        # Fertilizer calculation:
        # Total fertilizer = 50 * 1.5 = 75 kg
        # Nitrogen = 75 * 0.46 = 34.5 kg N
        # N2O-N = 34.5 * 0.01 = 0.345 kg N2O-N
        # N2O = 0.345 * (44/28) = 0.5421 kg N2O
        # CO2e = 0.5421 * 298 = 161.56 kg CO2e
        
        # Irrigation calculation:
        # Total irrigation = 30000 * 1.5 = 45,000 liters
        # CO2e = (45000 / 1000) * 0.5 = 22.5 kg CO2e
        
        expected_fertilizer = 161.56
        expected_irrigation = 22.5
        expected_total = expected_fertilizer + expected_irrigation
        
        assert abs(result['fertilizerEmissions'] - expected_fertilizer) < 0.1
        assert result['irrigationEmissions'] == expected_irrigation
        assert abs(result['totalEmissions'] - expected_total) < 0.1
    
    def test_zero_emissions(self):
        """Test emissions calculation with zero inputs"""
        from biomass_calculator import calculate_emissions
        
        metadata = {
            "fertilizerUsage": 0.0,
            "irrigationActivity": 0.0,
            "farmSizeHectares": 2.0
        }
        
        result = calculate_emissions(metadata)
        
        assert result['fertilizerEmissions'] == 0.0
        assert result['irrigationEmissions'] == 0.0
        assert result['totalEmissions'] == 0.0
    
    def test_emissions_precision(self):
        """Test that emissions are rounded to 2 decimal places"""
        from biomass_calculator import calculate_emissions
        
        metadata = {
            "fertilizerUsage": 123.456,  # Odd value to test rounding
            "irrigationActivity": 12345.678,
            "farmSizeHectares": 1.234
        }
        
        result = calculate_emissions(metadata)
        
        # Verify all values have at most 2 decimal places
        assert len(str(result['fertilizerEmissions']).split('.')[-1]) <= 2
        assert len(str(result['irrigationEmissions']).split('.')[-1]) <= 2
        assert len(str(result['totalEmissions']).split('.')[-1]) <= 2
    
    def test_large_farm_emissions(self):
        """Test emissions for large farm"""
        from biomass_calculator import calculate_emissions
        
        metadata = {
            "fertilizerUsage": 200.0,  # kg/hectare/year
            "irrigationActivity": 100000.0,  # liters/hectare/year
            "farmSizeHectares": 10.0
        }
        
        result = calculate_emissions(metadata)
        
        # Should have significant emissions
        assert result['fertilizerEmissions'] > 1000
        assert result['irrigationEmissions'] > 100
        assert result['totalEmissions'] > 1100
    
    def test_small_farm_emissions(self):
        """Test emissions for small farm"""
        from biomass_calculator import calculate_emissions
        
        metadata = {
            "fertilizerUsage": 20.0,  # kg/hectare/year
            "irrigationActivity": 5000.0,  # liters/hectare/year
            "farmSizeHectares": 0.5
        }
        
        result = calculate_emissions(metadata)
        
        # Should have small emissions
        assert result['fertilizerEmissions'] < 100
        assert result['irrigationEmissions'] < 10
        assert result['totalEmissions'] < 110
    
    def test_missing_optional_fields(self):
        """Test that missing fertilizer/irrigation fields default to 0"""
        from biomass_calculator import calculate_emissions
        
        # Only provide farm size
        metadata = {
            "farmSizeHectares": 2.0
        }
        
        result = calculate_emissions(metadata)
        
        # Should handle missing fields gracefully
        assert result['fertilizerEmissions'] == 0.0
        assert result['irrigationEmissions'] == 0.0
        assert result['totalEmissions'] == 0.0



# Property-Based Tests
from hypothesis import given, strategies as st, settings


class TestEmissionsPropertyTests:
    """Property-based tests for emissions calculation"""
    
    @given(
        fertilizer_usage=st.floats(min_value=0.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        irrigation_activity=st.floats(min_value=0.0, max_value=200000.0, allow_nan=False, allow_infinity=False),
        farm_size_hectares=st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_18_ipcc_emission_factor_usage(self, fertilizer_usage, irrigation_activity, farm_size_hectares):
        """
        Feature: carbon-ready, Property 18: IPCC Emission Factor Usage
        
        For any emissions calculation, the system SHALL use IPCC emission factors 
        for both fertilizer-related and irrigation-related emissions.
        
        **Validates: Requirements 7.1, 7.2**
        
        This property verifies that:
        1. Fertilizer emissions use IPCC Tier 1 factor (0.01 for N2O)
        2. N2O is converted to CO2e using GWP of 298
        3. Irrigation emissions use energy factor of 0.5 kg CO2/1000L
        4. The calculation follows the exact IPCC methodology
        """
        from biomass_calculator import calculate_emissions, EMISSION_FACTORS
        
        metadata = {
            "fertilizerUsage": fertilizer_usage,
            "irrigationActivity": irrigation_activity,
            "farmSizeHectares": farm_size_hectares
        }
        
        result = calculate_emissions(metadata)
        
        # Manually calculate expected values using IPCC factors
        # Fertilizer emissions calculation
        total_fertilizer_kg = fertilizer_usage * farm_size_hectares
        nitrogen_applied = total_fertilizer_kg * 0.46  # 46% N content in urea
        n2o_n_emissions = nitrogen_applied * EMISSION_FACTORS["fertilizer_n2o"]  # IPCC Tier 1: 0.01
        n2o_emissions = n2o_n_emissions * (44/28)  # Convert N2O-N to N2O
        expected_fertilizer_co2e = n2o_emissions * EMISSION_FACTORS["n2o_to_co2e"]  # GWP: 298
        
        # Irrigation emissions calculation
        total_irrigation_liters = irrigation_activity * farm_size_hectares
        expected_irrigation_co2e = (total_irrigation_liters / 1000) * EMISSION_FACTORS["irrigation_energy"]  # 0.5 kg CO2/1000L
        
        # Verify IPCC factors are used correctly
        # Allow small floating point tolerance
        assert abs(result['fertilizerEmissions'] - round(expected_fertilizer_co2e, 2)) < 0.01, \
            f"Fertilizer emissions {result['fertilizerEmissions']} does not match expected {round(expected_fertilizer_co2e, 2)}"
        
        assert abs(result['irrigationEmissions'] - round(expected_irrigation_co2e, 2)) < 0.01, \
            f"Irrigation emissions {result['irrigationEmissions']} does not match expected {round(expected_irrigation_co2e, 2)}"
        
        # Verify total is sum of components
        expected_total = round(expected_fertilizer_co2e + expected_irrigation_co2e, 2)
        assert abs(result['totalEmissions'] - expected_total) < 0.01, \
            f"Total emissions {result['totalEmissions']} does not match expected {expected_total}"
        
        # Verify IPCC factors are the correct values
        assert EMISSION_FACTORS["fertilizer_n2o"] == 0.01, "IPCC Tier 1 N2O factor must be 0.01 (1%)"
        assert EMISSION_FACTORS["n2o_to_co2e"] == 298, "N2O GWP must be 298"
        assert EMISSION_FACTORS["irrigation_energy"] == 0.5, "Irrigation energy factor must be 0.5 kg CO2/1000L"



class TestNetCarbonPosition:
    """Test net carbon position calculation"""
    
    def test_net_carbon_sink(self):
        """Test classification as Net Carbon Sink (positive position)"""
        from biomass_calculator import calculate_net_carbon_position
        
        result = calculate_net_carbon_position(
            annual_sequestration_co2e=5000.0,
            annual_emissions_co2e=2000.0
        )
        
        assert result['netPosition'] == 3000.0
        assert result['classification'] == "Net Carbon Sink"
        assert result['unit'] == "kg CO2e/year"
    
    def test_net_carbon_source(self):
        """Test classification as Net Carbon Source (negative position)"""
        from biomass_calculator import calculate_net_carbon_position
        
        result = calculate_net_carbon_position(
            annual_sequestration_co2e=1000.0,
            annual_emissions_co2e=3000.0
        )
        
        assert result['netPosition'] == -2000.0
        assert result['classification'] == "Net Carbon Source"
        assert result['unit'] == "kg CO2e/year"
    
    def test_zero_net_position(self):
        """Test zero net position (balanced)"""
        from biomass_calculator import calculate_net_carbon_position
        
        result = calculate_net_carbon_position(
            annual_sequestration_co2e=2500.0,
            annual_emissions_co2e=2500.0
        )
        
        assert result['netPosition'] == 0.0
        assert result['classification'] == "Net Carbon Sink"
        assert result['unit'] == "kg CO2e/year"
    
    def test_precision(self):
        """Test that result is rounded to 2 decimal places"""
        from biomass_calculator import calculate_net_carbon_position
        
        result = calculate_net_carbon_position(
            annual_sequestration_co2e=1234.567,
            annual_emissions_co2e=890.123
        )
        
        # Expected: 1234.567 - 890.123 = 344.444 -> 344.44
        assert result['netPosition'] == 344.44
        assert len(str(result['netPosition']).split('.')[-1]) <= 2


class TestNetCarbonPositionPropertyTests:
    """Property-based tests for net carbon position calculation"""
    
    @given(
        annual_sequestration_co2e=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        annual_emissions_co2e=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_22_net_carbon_position_calculation_accuracy(self, annual_sequestration_co2e, annual_emissions_co2e):
        """
        Feature: carbon-ready, Property 22: Net Carbon Position Calculation Accuracy
        
        For any farm with both annual sequestration increment and annual emissions data,
        the net carbon position SHALL equal the annual sequestration increment minus 
        the annual emissions.
        
        **Validates: Requirements 8.4**
        
        This property verifies that:
        1. Net position = sequestration - emissions (exact calculation)
        2. Result is stored in CO₂e kg/year
        3. Result has 2 decimal precision
        """
        from biomass_calculator import calculate_net_carbon_position
        
        result = calculate_net_carbon_position(
            annual_sequestration_co2e=annual_sequestration_co2e,
            annual_emissions_co2e=annual_emissions_co2e
        )
        
        # Calculate expected net position
        expected_net_position = annual_sequestration_co2e - annual_emissions_co2e
        
        # Verify calculation accuracy (with floating point tolerance)
        assert abs(result['netPosition'] - round(expected_net_position, 2)) < 0.01, \
            f"Net position {result['netPosition']} does not match expected {round(expected_net_position, 2)}"
        
        # Verify unit is correct
        assert result['unit'] == "kg CO2e/year", \
            f"Unit must be 'kg CO2e/year', got '{result['unit']}'"
        
        # Verify precision (2 decimal places)
        net_position_str = str(result['netPosition'])
        if '.' in net_position_str:
            decimal_places = len(net_position_str.split('.')[-1])
            assert decimal_places <= 2, \
                f"Net position must have at most 2 decimal places, got {decimal_places}"
        
        # Verify result structure
        assert 'netPosition' in result
        assert 'classification' in result
        assert 'unit' in result
    
    @given(
        annual_sequestration_co2e=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        annual_emissions_co2e=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_23_net_carbon_classification_logic(self, annual_sequestration_co2e, annual_emissions_co2e):
        """
        Feature: carbon-ready, Property 23: Net Carbon Classification Logic
        
        For any net carbon position calculation, the system SHALL classify the farm as 
        "Net Carbon Sink" if the position is positive, and "Net Carbon Source" if the 
        position is negative.
        
        **Validates: Requirements 8.5, 8.6**
        
        This property verifies that:
        1. Positive net position → "Net Carbon Sink"
        2. Negative net position → "Net Carbon Source"
        3. Zero net position → "Net Carbon Sink" (neutral case)
        4. Classification is consistent with the sign of net position
        """
        from biomass_calculator import calculate_net_carbon_position
        
        result = calculate_net_carbon_position(
            annual_sequestration_co2e=annual_sequestration_co2e,
            annual_emissions_co2e=annual_emissions_co2e
        )
        
        net_position = result['netPosition']
        classification = result['classification']
        
        # Verify classification logic based on net position sign
        if net_position > 0:
            assert classification == "Net Carbon Sink", \
                f"Positive net position {net_position} must be classified as 'Net Carbon Sink', got '{classification}'"
        elif net_position < 0:
            assert classification == "Net Carbon Source", \
                f"Negative net position {net_position} must be classified as 'Net Carbon Source', got '{classification}'"
        else:  # net_position == 0
            # Zero is treated as neutral sink
            assert classification == "Net Carbon Sink", \
                f"Zero net position must be classified as 'Net Carbon Sink', got '{classification}'"
        
        # Verify classification is one of the two valid values
        assert classification in ["Net Carbon Sink", "Net Carbon Source"], \
            f"Classification must be either 'Net Carbon Sink' or 'Net Carbon Source', got '{classification}'"



# ============================================================================
# Carbon Readiness Index (CRI) Tests
# ============================================================================

class TestCRIWeightManagement:
    """Unit tests for CRI weight management functions"""
    
    def test_get_default_weights(self):
        """Test that default weights are returned when no DB connection"""
        weights = bc.get_cri_weights(dynamodb_client=None)
        
        assert weights["netCarbonPosition"] == 0.5
        assert weights["socTrend"] == 0.3
        assert weights["managementPractices"] == 0.2
        assert abs(sum(weights.values()) - 1.0) < 0.001
    
    def test_set_weights_admin_authorization(self):
        """Test that only admin can set weights"""
        weights = {
            "netCarbonPosition": 0.6,
            "socTrend": 0.25,
            "managementPractices": 0.15
        }
        
        # Non-admin should raise PermissionError
        with pytest.raises(PermissionError):
            bc.set_cri_weights(weights, user_role="farmer")
    
    def test_set_weights_validation_sum(self):
        """Test that weights must sum to 1.0"""
        weights = {
            "netCarbonPosition": 0.6,
            "socTrend": 0.3,
            "managementPractices": 0.2  # Sum = 1.1
        }
        
        with pytest.raises(ValueError, match="must sum to 1.0"):
            bc.set_cri_weights(weights, user_role="admin")
    
    def test_set_weights_tolerance(self):
        """Test that weights within 0.001 tolerance are accepted"""
        # This should pass (sum = 1.0001, within tolerance)
        weights = {
            "netCarbonPosition": 0.5001,
            "socTrend": 0.3,
            "managementPractices": 0.2
        }
        
        # Should not raise ValueError (but may fail on DB connection)
        try:
            result = bc.set_cri_weights(weights, user_role="admin")
            # If DB connection fails, that's okay for this test
            assert result is not None
        except ValueError:
            pytest.fail("Weights within tolerance should not raise ValueError")


class TestNetPositionNormalization:
    """Unit tests for net position normalization"""
    
    def test_zero_net_position(self):
        """Test that zero net position maps to score of 50"""
        score = bc.normalize_net_position(0, farm_size_hectares=1.0)
        assert score == 50.0
    
    def test_positive_net_position(self):
        """Test that positive net position maps to score > 50"""
        score = bc.normalize_net_position(500, farm_size_hectares=1.0)
        assert 50 < score < 100
    
    def test_negative_net_position(self):
        """Test that negative net position maps to score < 50"""
        score = bc.normalize_net_position(-500, farm_size_hectares=1.0)
        assert 0 < score < 50
    
    def test_max_net_position(self):
        """Test that +1000 kg CO2e/ha/year maps to score of 100"""
        score = bc.normalize_net_position(1000, farm_size_hectares=1.0)
        assert score == 100.0
    
    def test_min_net_position(self):
        """Test that -1000 kg CO2e/ha/year maps to score of 0"""
        score = bc.normalize_net_position(-1000, farm_size_hectares=1.0)
        assert score == 0.0
    
    def test_per_hectare_normalization(self):
        """Test that normalization is per-hectare"""
        # Same per-hectare value should give same score
        score1 = bc.normalize_net_position(500, farm_size_hectares=1.0)
        score2 = bc.normalize_net_position(1000, farm_size_hectares=2.0)
        assert abs(score1 - score2) < 0.01
    
    def test_clamping_above_max(self):
        """Test that values above +1000/ha are clamped to 100"""
        score = bc.normalize_net_position(2000, farm_size_hectares=1.0)
        assert score == 100.0
    
    def test_clamping_below_min(self):
        """Test that values below -1000/ha are clamped to 0"""
        score = bc.normalize_net_position(-2000, farm_size_hectares=1.0)
        assert score == 0.0


class TestManagementPracticesScoring:
    """Unit tests for management practices scoring"""
    
    def test_optimal_practices(self):
        """Test that optimal practices score 100"""
        score = bc.score_management_practices(
            fertilizer_usage=100,  # Within 50-150 range
            irrigation_activity=10000  # Within 5000-15000 range
        )
        assert score == 100.0
    
    def test_zero_practices(self):
        """Test that zero usage scores low"""
        score = bc.score_management_practices(
            fertilizer_usage=0,
            irrigation_activity=0
        )
        assert score < 50
    
    def test_over_fertilization_penalty(self):
        """Test that over-fertilization is penalized"""
        optimal_score = bc.score_management_practices(100, 10000)
        over_score = bc.score_management_practices(300, 10000)
        assert over_score < optimal_score


class TestCRICalculation:
    """Unit tests for CRI calculation"""
    
    def test_excellent_classification(self):
        """Test that high scores classify as Excellent"""
        result = bc.calculate_carbon_readiness_index(
            net_position=800,  # High positive
            soc_trend={"status": "Improving"},
            management_practices={
                "fertilizerUsage": 100,
                "irrigationActivity": 10000,
                "farmSizeHectares": 1.0
            }
        )
        
        assert result["classification"] == "Excellent"
        assert result["score"] >= 70
    
    def test_needs_improvement_classification(self):
        """Test that low scores classify as Needs Improvement"""
        result = bc.calculate_carbon_readiness_index(
            net_position=-800,  # High negative
            soc_trend={"status": "Declining"},
            management_practices={
                "fertilizerUsage": 0,
                "irrigationActivity": 0,
                "farmSizeHectares": 1.0
            }
        )
        
        assert result["classification"] == "Needs Improvement"
        assert result["score"] < 40
    
    def test_moderate_classification(self):
        """Test that medium scores classify as Moderate"""
        result = bc.calculate_carbon_readiness_index(
            net_position=0,  # Neutral
            soc_trend={"status": "Stable"},
            management_practices={
                "fertilizerUsage": 100,
                "irrigationActivity": 10000,
                "farmSizeHectares": 1.0
            }
        )
        
        assert result["classification"] == "Moderate"
        assert 40 <= result["score"] < 70
    
    def test_component_breakdown(self):
        """Test that CRI includes component breakdown"""
        result = bc.calculate_carbon_readiness_index(
            net_position=500,
            soc_trend={"status": "Improving"},
            management_practices={
                "fertilizerUsage": 100,
                "irrigationActivity": 10000,
                "farmSizeHectares": 1.0
            }
        )
        
        assert "components" in result
        assert "netCarbonPosition" in result["components"]
        assert "socTrend" in result["components"]
        assert "managementPractices" in result["components"]
    
    def test_weights_included(self):
        """Test that CRI result includes weights used"""
        result = bc.calculate_carbon_readiness_index(
            net_position=500,
            soc_trend={"status": "Improving"},
            management_practices={
                "fertilizerUsage": 100,
                "irrigationActivity": 10000,
                "farmSizeHectares": 1.0
            }
        )
        
        assert "weights" in result
        assert "netCarbonPosition" in result["weights"]
        assert "socTrend" in result["weights"]
        assert "managementPractices" in result["weights"]
    
    def test_custom_weights(self):
        """Test that custom weights are used when provided"""
        custom_weights = {
            "netCarbonPosition": 0.6,
            "socTrend": 0.25,
            "managementPractices": 0.15
        }
        
        result = bc.calculate_carbon_readiness_index(
            net_position=500,
            soc_trend={"status": "Improving"},
            management_practices={
                "fertilizerUsage": 100,
                "irrigationActivity": 10000,
                "farmSizeHectares": 1.0
            },
            weights=custom_weights
        )
        
        assert result["weights"]["netCarbonPosition"] == 0.6
    
    def test_invalid_weights_fallback(self):
        """Test that invalid weights fall back to defaults"""
        invalid_weights = {
            "netCarbonPosition": 0.6,
            "socTrend": 0.3,
            "managementPractices": 0.2  # Sum = 1.1
        }
        
        result = bc.calculate_carbon_readiness_index(
            net_position=500,
            soc_trend={"status": "Improving"},
            management_practices={
                "fertilizerUsage": 100,
                "irrigationActivity": 10000,
                "farmSizeHectares": 1.0
            },
            weights=invalid_weights
        )
        
        # Should fall back to default weights
        assert result["weights"]["netCarbonPosition"] == 0.5


class TestCRIPropertyTests:
    """Property-based tests for CRI module"""
    
    @given(
        ncp_weight=st.floats(min_value=0.0, max_value=1.0),
        soc_weight=st.floats(min_value=0.0, max_value=1.0),
        mgmt_weight=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_25_cri_weight_validation_and_default_fallback(
        self, ncp_weight, soc_weight, mgmt_weight
    ):
        """
        Feature: carbon-ready, Property 25: CRI Weight Validation and Default Fallback
        
        **Validates: Requirements 9.2, 9.3, 9.4**
        
        For any Carbon Readiness Index calculation, if custom weighting parameters 
        are provided, the system SHALL validate that weights sum to 100%; if validation 
        fails or no weights are provided, the system SHALL use default weights 
        (50% Net Carbon Position, 30% SOC trend, 20% management practices).
        """
        weights = {
            "netCarbonPosition": ncp_weight,
            "socTrend": soc_weight,
            "managementPractices": mgmt_weight
        }
        
        weight_sum = ncp_weight + soc_weight + mgmt_weight
        
        # Test data
        net_position = 500
        soc_trend = {"status": "Improving"}
        management_practices = {
            "fertilizerUsage": 100,
            "irrigationActivity": 10000,
            "farmSizeHectares": 1.0
        }
        
        # Pass None to avoid AWS calls in tests
        result = bc.calculate_carbon_readiness_index(
            net_position=net_position,
            soc_trend=soc_trend,
            management_practices=management_practices,
            weights=weights,
            dynamodb_client=None
        )
        
        # Property: If weights don't sum to 1.0 (within tolerance), 
        # system should fall back to defaults
        if abs(weight_sum - 1.0) > 0.001:
            # Should use default weights
            assert result["weights"]["netCarbonPosition"] == 0.5
            assert result["weights"]["socTrend"] == 0.3
            assert result["weights"]["managementPractices"] == 0.2
        else:
            # Should use provided weights
            assert abs(result["weights"]["netCarbonPosition"] - ncp_weight) < 0.001
            assert abs(result["weights"]["socTrend"] - soc_weight) < 0.001
            assert abs(result["weights"]["managementPractices"] - mgmt_weight) < 0.001
        
        # Property: Weights in result must always sum to 1.0
        result_weight_sum = (
            result["weights"]["netCarbonPosition"] +
            result["weights"]["socTrend"] +
            result["weights"]["managementPractices"]
        )
        assert abs(result_weight_sum - 1.0) < 0.001


class TestCRIComponentCompletenessPropertyTest:
    """Property test for CRI component completeness"""
    
    @given(
        net_position=st.floats(min_value=-2000, max_value=2000, allow_nan=False, allow_infinity=False),
        soc_status=st.sampled_from(["Improving", "Stable", "Declining", "Insufficient Data"]),
        fertilizer_usage=st.floats(min_value=0, max_value=500, allow_nan=False, allow_infinity=False),
        irrigation_activity=st.floats(min_value=0, max_value=30000, allow_nan=False, allow_infinity=False),
        farm_size_hectares=st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_24_cri_component_completeness(
        self, net_position, soc_status, fertilizer_usage, 
        irrigation_activity, farm_size_hectares
    ):
        """
        Feature: carbon-ready, Property 24: CRI Component Completeness
        
        **Validates: Requirements 9.1**
        
        For any Carbon Readiness Index calculation, the system SHALL use all 
        three components: Net Carbon Position, Soil Organic Carbon trend, 
        and management practices data.
        """
        soc_trend = {"status": soc_status}
        management_practices = {
            "fertilizerUsage": fertilizer_usage,
            "irrigationActivity": irrigation_activity,
            "farmSizeHectares": farm_size_hectares
        }
        
        result = bc.calculate_carbon_readiness_index(
            net_position=net_position,
            soc_trend=soc_trend,
            management_practices=management_practices,
            dynamodb_client=None
        )
        
        # Property: Result must include all three components
        assert "components" in result
        assert "netCarbonPosition" in result["components"]
        assert "socTrend" in result["components"]
        assert "managementPractices" in result["components"]
        
        # Property: All component scores must be between 0 and 100
        assert 0 <= result["components"]["netCarbonPosition"] <= 100
        assert 0 <= result["components"]["socTrend"] <= 100
        assert 0 <= result["components"]["managementPractices"] <= 100
        
        # Property: Final score must be weighted sum of components
        expected_score = (
            result["components"]["netCarbonPosition"] * result["weights"]["netCarbonPosition"] +
            result["components"]["socTrend"] * result["weights"]["socTrend"] +
            result["components"]["managementPractices"] * result["weights"]["managementPractices"]
        )
        assert abs(result["score"] - expected_score) < 0.1


class TestCRIClassificationThresholdsPropertyTest:
    """Property test for CRI classification thresholds"""
    
    @given(
        net_position=st.floats(min_value=-2000, max_value=2000, allow_nan=False, allow_infinity=False),
        soc_status=st.sampled_from(["Improving", "Stable", "Declining", "Insufficient Data"]),
        fertilizer_usage=st.floats(min_value=0, max_value=500, allow_nan=False, allow_infinity=False),
        irrigation_activity=st.floats(min_value=0, max_value=30000, allow_nan=False, allow_infinity=False),
        farm_size_hectares=st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_28_cri_classification_thresholds(
        self, net_position, soc_status, fertilizer_usage,
        irrigation_activity, farm_size_hectares
    ):
        """
        Feature: carbon-ready, Property 28: CRI Classification Thresholds
        
        **Validates: Requirements 9.8, 9.9, 9.10**
        
        For any Carbon Readiness Index score, the system SHALL classify it as 
        "Needs Improvement" if score < 40, "Moderate" if 40 ≤ score < 70, 
        and "Excellent" if score ≥ 70.
        """
        soc_trend = {"status": soc_status}
        management_practices = {
            "fertilizerUsage": fertilizer_usage,
            "irrigationActivity": irrigation_activity,
            "farmSizeHectares": farm_size_hectares
        }
        
        result = bc.calculate_carbon_readiness_index(
            net_position=net_position,
            soc_trend=soc_trend,
            management_practices=management_practices,
            dynamodb_client=None
        )
        
        score = result["score"]
        classification = result["classification"]
        
        # Property: Classification must match score thresholds
        if score < 40:
            assert classification == "Needs Improvement", \
                f"Score {score} should be 'Needs Improvement' but got '{classification}'"
        elif score < 70:
            assert classification == "Moderate", \
                f"Score {score} should be 'Moderate' but got '{classification}'"
        else:
            assert classification == "Excellent", \
                f"Score {score} should be 'Excellent' but got '{classification}'"
        
        # Property: Score must be between 0 and 100
        assert 0 <= score <= 100, \
            f"Score {score} is outside valid range [0, 100]"
        
        # Property: Classification must be one of the three valid values
        assert classification in ["Needs Improvement", "Moderate", "Excellent"], \
            f"Invalid classification: {classification}"
