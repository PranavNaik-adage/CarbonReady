"""
Unit tests for biomass_calculator module
"""
import pytest
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
from hypothesis import given, strategies as st


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
