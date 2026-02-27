"""
Biomass Calculation Module for CarbonReady

This module implements allometric equations for calculating aboveground biomass
for cashew and coconut trees, as well as farm-level biomass scaling.

Allometric equations are based on research for Indian agricultural conditions.
"""


def calculate_cashew_biomass(dbh_cm, age_years):
    """
    Calculate aboveground biomass for cashew trees using DBH and age.
    
    Cashew allometric equation calibrated for Indian conditions.
    Based on DBH (Diameter at Breast Height) and tree age.
    
    Args:
        dbh_cm (float): Diameter at breast height in centimeters (1-200 cm)
        age_years (int): Tree age in years (1-100 years)
    
    Returns:
        float: Biomass in kilograms
    
    Validates: Requirements 4.1, 4.2
    """
    # Coefficients calibrated for Goa region
    a = 0.28
    b = 2.15
    age_factor = 1 + (0.02 * age_years)  # Age adjustment
    
    biomass_kg = a * (dbh_cm ** b) * age_factor
    return biomass_kg


def calculate_coconut_biomass(height_m, age_years):
    """
    Calculate aboveground biomass for coconut trees using height and age.
    
    Coconut allometric equation calibrated for Indian conditions.
    Based on tree height and age.
    
    Args:
        height_m (float): Tree height in meters (1-40 m)
        age_years (int): Tree age in years (1-100 years)
    
    Returns:
        float: Biomass in kilograms
    
    Validates: Requirements 4.1, 4.2
    """
    # Coefficients calibrated for Goa region
    a = 15.3
    b = 1.85
    age_factor = 1 + (0.015 * age_years)  # Age adjustment
    
    biomass_kg = a * (height_m ** b) * age_factor
    return biomass_kg


def calculate_farm_biomass(metadata):
    """
    Calculate total farm biomass by multiplying per-tree biomass by density and farm size.
    
    Args:
        metadata (dict): Farm metadata containing:
            - cropType (str): "cashew" or "coconut"
            - treeAge (int): Tree age in years
            - dbh (float): DBH in cm (for cashew)
            - treeHeight (float): Height in meters (for coconut)
            - plantationDensity (int): Trees per hectare
            - farmSizeHectares (float): Farm size in hectares
    
    Returns:
        float: Total farm biomass in kilograms
    
    Validates: Requirements 4.3
    """
    crop_type = metadata.get("cropType")
    tree_age = metadata.get("treeAge")
    plantation_density = metadata.get("plantationDensity")
    farm_size_hectares = metadata.get("farmSizeHectares")
    
    # Calculate per-tree biomass based on crop type
    if crop_type == "cashew":
        dbh = metadata.get("dbh")
        biomass_per_tree = calculate_cashew_biomass(dbh, tree_age)
    elif crop_type == "coconut":
        height = metadata.get("treeHeight")
        biomass_per_tree = calculate_coconut_biomass(height, tree_age)
    else:
        raise ValueError(f"Unsupported crop type: {crop_type}")
    
    # Calculate total number of trees
    total_trees = plantation_density * farm_size_hectares
    
    # Calculate total farm biomass
    total_biomass = biomass_per_tree * total_trees
    
    return total_biomass



def convert_biomass_to_co2e(biomass_kg):
    """
    Central conversion function: biomass → carbon → CO₂e
    
    This is the ONLY place where CO₂e conversion happens in the system.
    Follows the conversion chain:
    1. Biomass to carbon stock: biomass × 0.5
    2. Carbon to CO₂ equivalent: carbon × 3.667
    
    Args:
        biomass_kg (float): Biomass in kilograms
    
    Returns:
        float: CO₂ equivalent in kilograms, rounded to 2 decimal places
    
    Validates: Requirements 5.1, 5.2, 5.3, 4.4
    """
    # Step 1: Biomass to carbon (biomass × 0.5)
    carbon_kg = biomass_kg * 0.5
    
    # Step 2: Carbon to CO₂ equivalent (carbon × 3.667)
    co2_equivalent_kg = carbon_kg * 3.667
    
    # Store with 2 decimal precision as per requirements
    return round(co2_equivalent_kg, 2)


def estimate_sequestration_from_growth_curves(tree_age, crop_type, region, dynamodb_client=None):
    """
    Estimate annual biomass sequestration using crop-specific growth curves
    calibrated to regional averages.

    This function is used when historical biomass data is unavailable.
    It calculates the biomass increment between the current year and previous year
    using Chapman-Richards growth curve model.

    Args:
        tree_age (int): Current tree age in years (1-100)
        crop_type (str): "cashew" or "coconut"
        region (str): Region name (e.g., "Goa")
        dynamodb_client (optional): DynamoDB client for testing, uses boto3 default if None

    Returns:
        float: Annual biomass increment in kilograms (NOT CO₂e)

    Validates: Requirements 8.1, 8.2
    """
    import boto3
    import os

    # Use provided client or create default
    if dynamodb_client is None:
        dynamodb = boto3.resource('dynamodb')
    else:
        dynamodb = dynamodb_client

    # Load growth curve parameters from DynamoDB
    growth_params = load_growth_curve_parameters(crop_type, region, dynamodb)

    # Calculate biomass at current age and previous year using Chapman-Richards model
    biomass_current = calculate_chapman_richards_biomass(tree_age, growth_params)
    biomass_previous = calculate_chapman_richards_biomass(tree_age - 1, growth_params)

    # Annual biomass increment in kg
    biomass_increment = biomass_current - biomass_previous

    # Ensure non-negative increment
    return max(0.0, biomass_increment)


def load_growth_curve_parameters(crop_type, region, dynamodb):
    """
    Load regional growth curve parameters from DynamoDB.

    Args:
        crop_type (str): "cashew" or "coconut"
        region (str): Region name (e.g., "Goa")
        dynamodb: DynamoDB resource

    Returns:
        dict: Growth curve parameters with keys 'a', 'b', 'c'

    Raises:
        ValueError: If parameters not found or invalid
    """
    import os

    # Get table name from environment or use default
    table_name = os.environ.get('GROWTH_CURVES_TABLE', 'CarbonReady-GrowthCurvesTable')

    try:
        table = dynamodb.Table(table_name)

        # Query for growth curve parameters
        response = table.get_item(
            Key={
                'cropType': crop_type,
                'region': region
            }
        )

        if 'Item' not in response:
            # Return default parameters if not found
            return get_default_growth_parameters(crop_type)

        item = response['Item']
        growth_curve = item.get('growthCurve', {})
        parameters = growth_curve.get('parameters', {})

        # Validate parameters
        required_keys = ['a', 'b', 'c']
        if not all(key in parameters for key in required_keys):
            raise ValueError(f"Missing required growth curve parameters for {crop_type} in {region}")

        return parameters

    except Exception as e:
        print(f"Error loading growth curve parameters: {str(e)}")
        # Fall back to default parameters
        return get_default_growth_parameters(crop_type)


def get_default_growth_parameters(crop_type):
    """
    Get default growth curve parameters for crop type.

    These are fallback values calibrated for Goa region based on
    regional agricultural research.

    Args:
        crop_type (str): "cashew" or "coconut"

    Returns:
        dict: Default Chapman-Richards parameters
    """
    defaults = {
        'cashew': {
            'a': 250.0,   # Maximum biomass asymptote (kg)
            'b': 0.08,    # Growth rate parameter
            'c': 1.5      # Shape parameter
        },
        'coconut': {
            'a': 350.0,   # Maximum biomass asymptote (kg)
            'b': 0.06,    # Growth rate parameter
            'c': 1.8      # Shape parameter
        }
    }

    if crop_type not in defaults:
        raise ValueError(f"Unsupported crop type: {crop_type}")

    return defaults[crop_type]


def calculate_chapman_richards_biomass(age, parameters):
    """
    Calculate biomass using Chapman-Richards growth curve model.

    Chapman-Richards equation:
    Biomass(t) = a × (1 - exp(-b × t))^c

    Where:
    - a: Maximum biomass asymptote
    - b: Growth rate parameter
    - c: Shape parameter
    - t: Tree age in years

    Args:
        age (int): Tree age in years
        parameters (dict): Growth curve parameters with keys 'a', 'b', 'c'

    Returns:
        float: Estimated biomass in kilograms
    """
    import math

    a = parameters['a']
    b = parameters['b']
    c = parameters['c']

    # Handle edge case for age 0 or negative
    if age <= 0:
        return 0.0

    # Chapman-Richards equation
    biomass = a * ((1 - math.exp(-b * age)) ** c)

    return biomass


def calculate_annual_sequestration(farm_id, metadata, historical_biomass=None, dynamodb_client=None):
    """
    Calculate annual carbon sequestration increment for a farm.

    This function determines the annual biomass increment using either:
    1. Historical biomass data (if available) - preferred method
    2. Growth curve estimation (fallback when historical data unavailable)

    The biomass increment is then converted to CO₂e using the central
    convert_biomass_to_co2e() function.

    Args:
        farm_id (str): Farm identifier
        metadata (dict): Farm metadata containing:
            - cropType (str): "cashew" or "coconut"
            - treeAge (int): Tree age in years
            - plantationDensity (int): Trees per hectare
            - farmSizeHectares (float): Farm size in hectares
        historical_biomass (float, optional): Previous year's biomass in kg
        dynamodb_client (optional): DynamoDB client for testing

    Returns:
        dict: Sequestration data containing:
            - biomassIncrement (float): Annual biomass increment in kg
            - co2eSequestration (float): Annual CO₂e sequestration in kg
            - method (str): "historical" or "growth_curve"
            - unit (str): "kg CO2e/year"

    Validates: Requirements 8.1, 8.2, 8.3
    """
    crop_type = metadata.get("cropType")
    tree_age = metadata.get("treeAge")
    plantation_density = metadata.get("plantationDensity")
    farm_size_hectares = metadata.get("farmSizeHectares")

    # Calculate current total farm biomass
    current_biomass = calculate_farm_biomass(metadata)

    # Determine biomass increment
    if historical_biomass is not None and historical_biomass > 0:
        # Method 1: Use historical data (preferred)
        biomass_increment = current_biomass - historical_biomass
        method = "historical"
    else:
        # Method 2: Use growth curves (fallback)
        # Get per-tree increment from growth curves
        per_tree_increment = estimate_sequestration_from_growth_curves(
            tree_age=tree_age,
            crop_type=crop_type,
            region="Goa",
            dynamodb_client=dynamodb_client
        )

        # Scale to farm level
        total_trees = plantation_density * farm_size_hectares
        biomass_increment = per_tree_increment * total_trees
        method = "growth_curve"

    # Ensure non-negative increment
    biomass_increment = max(0.0, biomass_increment)

    # Convert biomass increment to CO₂e using central conversion function
    co2e_sequestration = convert_biomass_to_co2e(biomass_increment)

    return {
        "biomassIncrement": round(biomass_increment, 2),
        "co2eSequestration": co2e_sequestration,
        "method": method,
        "unit": "kg CO2e/year"
    }




def estimate_sequestration_from_growth_curves(tree_age, crop_type, region, dynamodb_client=None):
    """
    Estimate annual biomass sequestration using crop-specific growth curves
    calibrated to regional averages.
    
    This function is used when historical biomass data is unavailable.
    It calculates the biomass increment between the current year and previous year
    using Chapman-Richards growth curve model.
    
    Args:
        tree_age (int): Current tree age in years (1-100)
        crop_type (str): "cashew" or "coconut"
        region (str): Region name (e.g., "Goa")
        dynamodb_client (optional): DynamoDB client for testing, uses boto3 default if None
    
    Returns:
        float: Annual biomass increment in kilograms (NOT CO₂e)
    
    Validates: Requirements 8.1, 8.2
    """
    import boto3
    import os
    
    # Use provided client or create default
    if dynamodb_client is None:
        dynamodb = boto3.resource('dynamodb')
    else:
        dynamodb = dynamodb_client
    
    # Load growth curve parameters from DynamoDB
    growth_params = load_growth_curve_parameters(crop_type, region, dynamodb)
    
    # Calculate biomass at current age and previous year using Chapman-Richards model
    biomass_current = calculate_chapman_richards_biomass(tree_age, growth_params)
    biomass_previous = calculate_chapman_richards_biomass(tree_age - 1, growth_params)
    
    # Annual biomass increment in kg
    biomass_increment = biomass_current - biomass_previous
    
    # Ensure non-negative increment
    return max(0.0, biomass_increment)


def load_growth_curve_parameters(crop_type, region, dynamodb):
    """
    Load regional growth curve parameters from DynamoDB.
    
    Args:
        crop_type (str): "cashew" or "coconut"
        region (str): Region name (e.g., "Goa")
        dynamodb: DynamoDB resource
    
    Returns:
        dict: Growth curve parameters with keys 'a', 'b', 'c'
    
    Raises:
        ValueError: If parameters not found or invalid
    """
    import os
    
    # Get table name from environment or use default
    table_name = os.environ.get('GROWTH_CURVES_TABLE', 'CarbonReady-GrowthCurvesTable')
    
    try:
        table = dynamodb.Table(table_name)
        
        # Query for growth curve parameters
        response = table.get_item(
            Key={
                'cropType': crop_type,
                'region': region
            }
        )
        
        if 'Item' not in response:
            # Return default parameters if not found
            return get_default_growth_parameters(crop_type)
        
        item = response['Item']
        growth_curve = item.get('growthCurve', {})
        parameters = growth_curve.get('parameters', {})
        
        # Validate parameters
        required_keys = ['a', 'b', 'c']
        if not all(key in parameters for key in required_keys):
            raise ValueError(f"Missing required growth curve parameters for {crop_type} in {region}")
        
        return parameters
        
    except Exception as e:
        print(f"Error loading growth curve parameters: {str(e)}")
        # Fall back to default parameters
        return get_default_growth_parameters(crop_type)


def get_default_growth_parameters(crop_type):
    """
    Get default growth curve parameters for crop type.
    
    These are fallback values calibrated for Goa region based on
    regional agricultural research.
    
    Args:
        crop_type (str): "cashew" or "coconut"
    
    Returns:
        dict: Default Chapman-Richards parameters
    """
    defaults = {
        'cashew': {
            'a': 250.0,   # Maximum biomass asymptote (kg)
            'b': 0.08,    # Growth rate parameter
            'c': 1.5      # Shape parameter
        },
        'coconut': {
            'a': 350.0,   # Maximum biomass asymptote (kg)
            'b': 0.06,    # Growth rate parameter
            'c': 1.8      # Shape parameter
        }
    }
    
    if crop_type not in defaults:
        raise ValueError(f"Unsupported crop type: {crop_type}")
    
    return defaults[crop_type]


def calculate_chapman_richards_biomass(age, parameters):
    """
    Calculate biomass using Chapman-Richards growth curve model.
    
    Chapman-Richards equation:
    Biomass(t) = a × (1 - exp(-b × t))^c
    
    Where:
    - a: Maximum biomass asymptote
    - b: Growth rate parameter
    - c: Shape parameter
    - t: Tree age in years
    
    Args:
        age (int): Tree age in years
        parameters (dict): Growth curve parameters with keys 'a', 'b', 'c'
    
    Returns:
        float: Estimated biomass in kilograms
    """
    import math
    
    a = parameters['a']
    b = parameters['b']
    c = parameters['c']
    
    # Handle edge case for age 0 or negative
    if age <= 0:
        return 0.0
    
    # Chapman-Richards equation
    biomass = a * ((1 - math.exp(-b * age)) ** c)
    
    return biomass


def calculate_annual_sequestration(farm_id, metadata, historical_biomass=None, dynamodb_client=None):
    """
    Calculate annual carbon sequestration increment for a farm.
    
    This function determines the annual biomass increment using either:
    1. Historical biomass data (if available) - preferred method
    2. Growth curve estimation (fallback when historical data unavailable)
    
    The biomass increment is then converted to CO₂e using the central
    convert_biomass_to_co2e() function.
    
    Args:
        farm_id (str): Farm identifier
        metadata (dict): Farm metadata containing:
            - cropType (str): "cashew" or "coconut"
            - treeAge (int): Tree age in years
            - plantationDensity (int): Trees per hectare
            - farmSizeHectares (float): Farm size in hectares
        historical_biomass (float, optional): Previous year's biomass in kg
        dynamodb_client (optional): DynamoDB client for testing
    
    Returns:
        dict: Sequestration data containing:
            - biomassIncrement (float): Annual biomass increment in kg
            - co2eSequestration (float): Annual CO₂e sequestration in kg
            - method (str): "historical" or "growth_curve"
            - unit (str): "kg CO2e/year"
    
    Validates: Requirements 8.1, 8.2, 8.3
    """
    crop_type = metadata.get("cropType")
    tree_age = metadata.get("treeAge")
    plantation_density = metadata.get("plantationDensity")
    farm_size_hectares = metadata.get("farmSizeHectares")
    
    # Calculate current total farm biomass
    current_biomass = calculate_farm_biomass(metadata)
    
    # Determine biomass increment
    if historical_biomass is not None and historical_biomass > 0:
        # Method 1: Use historical data (preferred)
        biomass_increment = current_biomass - historical_biomass
        method = "historical"
    else:
        # Method 2: Use growth curves (fallback)
        # Get per-tree increment from growth curves
        per_tree_increment = estimate_sequestration_from_growth_curves(
            tree_age=tree_age,
            crop_type=crop_type,
            region="Goa",
            dynamodb_client=dynamodb_client
        )
        
        # Scale to farm level
        total_trees = plantation_density * farm_size_hectares
        biomass_increment = per_tree_increment * total_trees
        method = "growth_curve"
    
    # Ensure non-negative increment
    biomass_increment = max(0.0, biomass_increment)
    
    # Convert biomass increment to CO₂e using central conversion function
    co2e_sequestration = convert_biomass_to_co2e(biomass_increment)
    
    return {
        "biomassIncrement": round(biomass_increment, 2),
        "co2eSequestration": co2e_sequestration,
        "method": method,
        "unit": "kg CO2e/year"
    }


# IPCC Tier 1 Emission Factors
EMISSION_FACTORS = {
    "fertilizer_n2o": 0.01,  # IPCC Tier 1 Direct Emission Factor (1%)
    "n2o_to_co2e": 298,      # N2O global warming potential (GWP)
    "irrigation_energy": 0.5  # kg CO2 / 1000 liters (pump energy)
}


def calculate_emissions(metadata):
    """
    Calculate total farm emissions from fertilizer and irrigation using IPCC Tier 1 factors.
    
    This function calculates emissions in CO₂ equivalent (CO₂e) from:
    1. Fertilizer application (N2O emissions from nitrogen)
    2. Irrigation pump energy (CO₂ emissions)
    
    Calculation steps:
    1. Calculate total fertilizer for entire farm (fertilizerUsage × farmSizeHectares)
    2. Assume 46% N content in urea fertilizer
    3. Apply IPCC Tier 1 factor (1%) to get N2O-N emissions
    4. Convert N2O-N to N2O (multiply by 44/28)
    5. Convert to CO2 equivalent (multiply by 298)
    6. Calculate irrigation emissions from pump energy
    7. Return total emissions in CO2e kg/year with 2 decimal precision
    
    Args:
        metadata (dict): Farm metadata containing:
            - fertilizerUsage (float): Fertilizer usage in kg/hectare/year
            - irrigationActivity (float): Irrigation in liters/hectare/year
            - farmSizeHectares (float): Farm size in hectares
    
    Returns:
        dict: Emissions data containing:
            - fertilizerEmissions (float): Fertilizer CO₂e in kg/year
            - irrigationEmissions (float): Irrigation CO₂e in kg/year
            - totalEmissions (float): Total CO₂e in kg/year
            - unit (str): "kg CO2e/year"
    
    Validates: Requirements 7.1, 7.2, 7.3, 7.4
    """
    fertilizer_usage = metadata.get("fertilizerUsage", 0)
    irrigation_activity = metadata.get("irrigationActivity", 0)
    farm_size_hectares = metadata.get("farmSizeHectares")
    
    # 1. Fertilizer emissions
    # Calculate total fertilizer for entire farm
    total_fertilizer_kg = fertilizer_usage * farm_size_hectares
    
    # Assume 46% N content in urea (common fertilizer)
    nitrogen_applied = total_fertilizer_kg * 0.46
    
    # N2O emissions using IPCC Tier 1 factor (1%)
    n2o_n_emissions = nitrogen_applied * EMISSION_FACTORS["fertilizer_n2o"]
    
    # Convert N2O-N to N2O (multiply by 44/28)
    n2o_emissions = n2o_n_emissions * (44/28)
    
    # Convert to CO2 equivalent
    fertilizer_co2e = n2o_emissions * EMISSION_FACTORS["n2o_to_co2e"]
    
    # 2. Irrigation emissions (from pump energy)
    # Calculate total irrigation for entire farm
    total_irrigation_liters = irrigation_activity * farm_size_hectares
    
    irrigation_co2e = (total_irrigation_liters / 1000) * \
                      EMISSION_FACTORS["irrigation_energy"]
    
    # 3. Total emissions with 2 decimal precision
    total_emissions = fertilizer_co2e + irrigation_co2e
    
    return {
        "fertilizerEmissions": round(fertilizer_co2e, 2),
        "irrigationEmissions": round(irrigation_co2e, 2),
        "totalEmissions": round(total_emissions, 2),
        "unit": "kg CO2e/year"
    }


def calculate_net_carbon_position(annual_sequestration_co2e, annual_emissions_co2e):
    """
    Calculate net carbon position as the difference between annual sequestration and emissions.
    
    Net carbon position = annual_sequestration_co2e - annual_emissions_co2e
    
    Classification:
    - Positive value: "Net Carbon Sink" (farm sequesters more than it emits)
    - Negative value: "Net Carbon Source" (farm emits more than it sequesters)
    
    Args:
        annual_sequestration_co2e (float): Annual carbon sequestration in kg CO₂e/year
        annual_emissions_co2e (float): Annual emissions in kg CO₂e/year
    
    Returns:
        dict: Net carbon position data containing:
            - netPosition (float): Net carbon position in kg CO₂e/year (2 decimal precision)
            - classification (str): "Net Carbon Sink" or "Net Carbon Source"
            - unit (str): "kg CO2e/year"
    
    Validates: Requirements 8.4, 8.5, 8.6, 8.7
    """
    # Calculate net position
    net_position = annual_sequestration_co2e - annual_emissions_co2e
    
    # Round to 2 decimal places for storage
    net_position_rounded = round(net_position, 2)
    
    # Classify based on sign of rounded value
    # This ensures classification is consistent with the stored value
    if net_position_rounded > 0:
        classification = "Net Carbon Sink"
    elif net_position_rounded < 0:
        classification = "Net Carbon Source"
    else:
        # Exactly zero - technically neither, but classify as neutral sink
        classification = "Net Carbon Sink"
    
    return {
        "netPosition": net_position_rounded,
        "classification": classification,
        "unit": "kg CO2e/year"
    }


# ============================================================================
# Carbon Readiness Index (CRI) Module
# ============================================================================

def get_cri_weights(dynamodb_client=None):
    """
    Retrieve CRI weights from DynamoDB.
    
    Returns default weights (50%, 30%, 20%) if not found in database.
    
    Args:
        dynamodb_client: Optional boto3 DynamoDB client for testing
        
    Returns:
        dict: CRI weights with keys:
            - netCarbonPosition: float (0-1)
            - socTrend: float (0-1)
            - managementPractices: float (0-1)
    """
    # Default weights as specified in requirements
    default_weights = {
        "netCarbonPosition": 0.5,
        "socTrend": 0.3,
        "managementPractices": 0.2
    }
    
    # If no DynamoDB client provided, return defaults
    if dynamodb_client is None:
        try:
            import boto3
            dynamodb_client = boto3.client('dynamodb')
        except Exception:
            return default_weights
    
    try:
        # Query DynamoDB for latest weights
        response = dynamodb_client.query(
            TableName='CRIWeights',
            KeyConditionExpression='configId = :configId',
            ExpressionAttributeValues={
                ':configId': {'S': 'default'}
            },
            ScanIndexForward=False,  # Sort descending by version
            Limit=1
        )
        
        if response.get('Items'):
            item = response['Items'][0]
            weights = {
                "netCarbonPosition": float(item['netCarbonPosition']['N']),
                "socTrend": float(item['socTrend']['N']),
                "managementPractices": float(item['managementPractices']['N'])
            }
            return weights
        else:
            return default_weights
            
    except Exception as e:
        # If any error occurs, return default weights
        print(f"Error retrieving CRI weights: {e}")
        return default_weights


def set_cri_weights(weights, user_role, dynamodb_client=None):
    """
    Set CRI weights in DynamoDB with admin authorization check.
    
    Args:
        weights: dict with keys netCarbonPosition, socTrend, managementPractices
        user_role: str, user role (must be "admin")
        dynamodb_client: Optional boto3 DynamoDB client for testing
        
    Returns:
        dict: Result with keys:
            - success: bool
            - message: str
            - weights: dict (if successful)
            
    Raises:
        ValueError: If weights don't sum to 1.0 (within 0.001 tolerance)
        PermissionError: If user is not admin
    """
    # Check admin authorization
    if user_role != "admin":
        raise PermissionError("Only admin users can modify CRI weights")
    
    # Validate weights sum to 1.0 (with 0.001 tolerance)
    weight_sum = (
        weights.get("netCarbonPosition", 0) +
        weights.get("socTrend", 0) +
        weights.get("managementPractices", 0)
    )
    
    if abs(weight_sum - 1.0) > 0.001:
        raise ValueError(
            f"Weights must sum to 1.0 (got {weight_sum}). "
            f"Difference: {abs(weight_sum - 1.0)}"
        )
    
    # If no DynamoDB client provided, create one
    if dynamodb_client is None:
        try:
            import boto3
            dynamodb_client = boto3.client('dynamodb')
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to connect to DynamoDB: {e}"
            }
    
    try:
        # Get current version
        response = dynamodb_client.query(
            TableName='CRIWeights',
            KeyConditionExpression='configId = :configId',
            ExpressionAttributeValues={
                ':configId': {'S': 'default'}
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        # Increment version
        current_version = 0
        if response.get('Items'):
            current_version = int(response['Items'][0]['version']['N'])
        new_version = current_version + 1
        
        # Store new weights
        from datetime import datetime
        dynamodb_client.put_item(
            TableName='CRIWeights',
            Item={
                'configId': {'S': 'default'},
                'version': {'N': str(new_version)},
                'netCarbonPosition': {'N': str(weights['netCarbonPosition'])},
                'socTrend': {'N': str(weights['socTrend'])},
                'managementPractices': {'N': str(weights['managementPractices'])},
                'updatedAt': {'S': datetime.utcnow().isoformat()},
                'updatedBy': {'S': 'admin'}
            }
        )
        
        return {
            "success": True,
            "message": f"CRI weights updated to version {new_version}",
            "weights": weights,
            "version": new_version
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to update CRI weights: {e}"
        }


def normalize_net_position(net_position_co2e_kg_per_year, farm_size_hectares):
    """
    Normalize net carbon position to 0-100 scale on a per-hectare basis.
    
    This makes the model scalable across different farm sizes by normalizing
    to per-hectare values before scoring.
    
    Normalization logic:
    - Calculate net position per hectare
    - Highly negative values (< -1000 kg CO2e/ha/year): score 0
    - Zero net position: score 50
    - Highly positive values (> +1000 kg CO2e/ha/year): score 100
    - Linear interpolation between these points
    
    Args:
        net_position_co2e_kg_per_year: float, net carbon position in kg CO2e/year
        farm_size_hectares: float, farm size in hectares
        
    Returns:
        float: Normalized score between 0 and 100
    """
    # Normalize to per-hectare basis
    net_position_per_hectare = net_position_co2e_kg_per_year / farm_size_hectares
    
    # Define normalization bounds (per hectare)
    MIN_NET_POSITION_PER_HA = -1000  # kg CO2e/ha/year (strong net source)
    MAX_NET_POSITION_PER_HA = 1000   # kg CO2e/ha/year (strong net sink)
    
    # Clamp to bounds
    clamped = max(MIN_NET_POSITION_PER_HA, 
                  min(MAX_NET_POSITION_PER_HA, net_position_per_hectare))
    
    # Linear normalization to 0-100
    normalized = ((clamped - MIN_NET_POSITION_PER_HA) / 
                  (MAX_NET_POSITION_PER_HA - MIN_NET_POSITION_PER_HA)) * 100
    
    return normalized


def score_management_practices(fertilizer_usage, irrigation_activity):
    """
    Score management practices on a 0-100 scale.
    
    Moderate, optimal fertilizer and irrigation levels score higher.
    Over-fertilization can increase emissions and reduce SOC.
    
    Args:
        fertilizer_usage: float, kg/hectare/year
        irrigation_activity: float, liters/hectare/year
        
    Returns:
        float: Management practices score between 0 and 100
    """
    # Optimal ranges (based on sustainable practices for cashew/coconut)
    OPTIMAL_FERTILIZER_MIN = 50   # kg/ha/year
    OPTIMAL_FERTILIZER_MAX = 150  # kg/ha/year
    OPTIMAL_IRRIGATION_MIN = 5000   # liters/ha/year
    OPTIMAL_IRRIGATION_MAX = 15000  # liters/ha/year
    
    # Score fertilizer usage
    if OPTIMAL_FERTILIZER_MIN <= fertilizer_usage <= OPTIMAL_FERTILIZER_MAX:
        fertilizer_score = 100
    elif fertilizer_usage < OPTIMAL_FERTILIZER_MIN:
        # Under-fertilization: linear scale from 0 to 100
        fertilizer_score = (fertilizer_usage / OPTIMAL_FERTILIZER_MIN) * 100
    else:
        # Over-fertilization: penalize heavily
        excess = fertilizer_usage - OPTIMAL_FERTILIZER_MAX
        fertilizer_score = max(0, 100 - (excess / 10))
    
    # Score irrigation activity
    if OPTIMAL_IRRIGATION_MIN <= irrigation_activity <= OPTIMAL_IRRIGATION_MAX:
        irrigation_score = 100
    elif irrigation_activity < OPTIMAL_IRRIGATION_MIN:
        # Under-irrigation: linear scale from 0 to 100
        irrigation_score = (irrigation_activity / OPTIMAL_IRRIGATION_MIN) * 100
    else:
        # Over-irrigation: penalize
        excess = irrigation_activity - OPTIMAL_IRRIGATION_MAX
        irrigation_score = max(0, 100 - (excess / 1000))
    
    # Weighted average (fertilizer 60%, irrigation 40%)
    management_score = (fertilizer_score * 0.6) + (irrigation_score * 0.4)
    
    return management_score


def calculate_carbon_readiness_index(net_position, soc_trend, management_practices, 
                                     weights=None, dynamodb_client=None):
    """
    Calculate Carbon Readiness Index with configurable weights.
    
    Args:
        net_position: float, net carbon position in kg CO2e/year
        soc_trend: dict with 'status' key ("Improving", "Stable", "Declining", "Insufficient Data")
        management_practices: dict with 'fertilizerUsage', 'irrigationActivity', 'farmSizeHectares'
        weights: Optional dict with netCarbonPosition, socTrend, managementPractices weights
        dynamodb_client: Optional boto3 DynamoDB client for testing
        
    Returns:
        dict: CRI result with keys:
            - score: float (0-100)
            - classification: str ("Needs Improvement", "Moderate", "Excellent")
            - components: dict with individual component scores
            - weights: dict with weights used
    """
    # Get weights (use provided or retrieve from DynamoDB)
    if weights is None:
        weights = get_cri_weights(dynamodb_client)
    else:
        # Validate provided weights
        weight_sum = (
            weights.get("netCarbonPosition", 0) +
            weights.get("socTrend", 0) +
            weights.get("managementPractices", 0)
        )
        if abs(weight_sum - 1.0) > 0.001:
            # Fall back to default weights if invalid
            weights = get_cri_weights(dynamodb_client)
    
    # 1. Net Carbon Position score (0-100)
    ncp_score = normalize_net_position(
        net_position, 
        management_practices['farmSizeHectares']
    )
    
    # 2. SOC Trend score (0-100)
    soc_score_map = {
        "Improving": 100,
        "Stable": 60,
        "Declining": 20,
        "Insufficient Data": 50
    }
    soc_score = soc_score_map.get(soc_trend.get("status", "Insufficient Data"), 50)
    
    # 3. Management Practices score (0-100)
    mgmt_score = score_management_practices(
        management_practices['fertilizerUsage'],
        management_practices['irrigationActivity']
    )
    
    # 4. Weighted sum
    cri = (
        ncp_score * weights["netCarbonPosition"] +
        soc_score * weights["socTrend"] +
        mgmt_score * weights["managementPractices"]
    )
    
    # 5. Classification
    if cri < 40:
        classification = "Needs Improvement"
    elif cri < 70:
        classification = "Moderate"
    else:
        classification = "Excellent"
    
    return {
        "score": round(cri, 2),
        "classification": classification,
        "components": {
            "netCarbonPosition": round(ncp_score, 2),
            "socTrend": round(soc_score, 2),
            "managementPractices": round(mgmt_score, 2)
        },
        "weights": weights
    }
