"""
Unit tests for Dashboard API Lambda
Tests API endpoints, authentication, and authorization
"""
import json
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Set environment variables before importing index
os.environ['CARBON_CALCULATIONS_TABLE'] = 'test-carbon-calculations'
os.environ['SENSOR_DATA_TABLE'] = 'test-sensor-data'
os.environ['CRI_WEIGHTS_TABLE'] = 'test-cri-weights'

# Add lambda directory to path
sys.path.insert(0, os.path.dirname(__file__))

import index


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB resource"""
    with patch('index.dynamodb') as mock_db:
        yield mock_db


@pytest.fixture
def sample_carbon_calculation():
    """Sample carbon calculation data"""
    return {
        'farmId': 'farm-001',
        'calculatedAt': datetime.utcnow().isoformat() + 'Z',
        'netCarbonPosition': Decimal('1250.50'),
        'annualSequestration': Decimal('2000.00'),
        'emissions': {
            'fertilizerEmissions': Decimal('500.00'),
            'irrigationEmissions': Decimal('249.50'),
            'totalEmissions': Decimal('749.50')
        },
        'carbonStock': Decimal('5000.00'),
        'co2EquivalentStock': Decimal('18335.00'),
        'carbonReadinessIndex': {
            'score': Decimal('72.5'),
            'classification': 'Excellent',
            'components': {
                'netCarbonPosition': Decimal('85'),
                'socTrend': Decimal('60'),
                'managementPractices': Decimal('60')
            },
            'weights': {
                'netCarbonPosition': Decimal('0.5'),
                'socTrend': Decimal('0.3'),
                'managementPractices': Decimal('0.2')
            }
        },
        'socTrend': {
            'status': 'Stable',
            'score': Decimal('0.02')
        },
        'modelVersions': {
            'cri': 'v1.0.0'
        }
    }


@pytest.fixture
def sample_sensor_data():
    """Sample sensor data"""
    timestamp = int(datetime.utcnow().timestamp())
    return {
        'farmId': 'farm-001',
        'timestamp': timestamp,
        'deviceId': 'esp32-abc123',
        'soilMoisture': Decimal('45.5'),
        'soilTemperature': Decimal('24.3'),
        'airTemperature': Decimal('28.7'),
        'humidity': Decimal('65.2'),
        'validationStatus': 'valid'
    }


class TestCarbonPosition:
    """Tests for carbon position endpoint"""
    
    def test_get_carbon_position_success(self, mock_dynamodb, sample_carbon_calculation):
        """Test successful carbon position retrieval"""
        # Mock DynamoDB query
        mock_table = Mock()
        mock_table.query.return_value = {'Items': [sample_carbon_calculation]}
        mock_dynamodb.Table.return_value = mock_table
        
        # Call function
        result = index.get_carbon_position('farm-001')
        
        # Verify response
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['farmId'] == 'farm-001'
        assert body['netCarbonPosition'] == 1250.50
        assert body['classification'] == 'Net Carbon Sink'
        assert body['isStale'] == False
    
    def test_get_carbon_position_no_data(self, mock_dynamodb):
        """Test carbon position with no data"""
        mock_table = Mock()
        mock_table.query.return_value = {'Items': []}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.get_carbon_position('farm-999')
        
        assert result['statusCode'] == 404
        body = json.loads(result['body'])
        assert body['error']['code'] == 'NO_DATA'
    
    def test_get_carbon_position_stale_data(self, mock_dynamodb, sample_carbon_calculation):
        """Test carbon position with stale data (>24 hours old)"""
        # Set calculated time to 25 hours ago
        old_time = (datetime.utcnow() - timedelta(hours=25)).isoformat() + 'Z'
        sample_carbon_calculation['calculatedAt'] = old_time
        
        mock_table = Mock()
        mock_table.query.return_value = {'Items': [sample_carbon_calculation]}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.get_carbon_position('farm-001')
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['isStale'] == True


class TestCarbonReadinessIndex:
    """Tests for CRI endpoint"""
    
    def test_get_cri_success(self, mock_dynamodb, sample_carbon_calculation):
        """Test successful CRI retrieval with breakdown"""
        mock_table = Mock()
        mock_table.query.return_value = {'Items': [sample_carbon_calculation]}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.get_carbon_readiness_index('farm-001')
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['farmId'] == 'farm-001'
        assert body['carbonReadinessIndex']['score'] == 72.5
        assert body['carbonReadinessIndex']['classification'] == 'Excellent'
        
        # Verify component breakdown
        components = body['carbonReadinessIndex']['components']
        assert 'netCarbonPosition' in components
        assert 'socTrend' in components
        assert 'managementPractices' in components
        
        # Verify each component has score, weight, and contribution
        for component in components.values():
            assert 'score' in component
            assert 'weight' in component
            assert 'contribution' in component
    
    def test_get_cri_no_data(self, mock_dynamodb):
        """Test CRI with no data"""
        mock_table = Mock()
        mock_table.query.return_value = {'Items': []}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.get_carbon_readiness_index('farm-999')
        
        assert result['statusCode'] == 404
        body = json.loads(result['body'])
        assert body['error']['code'] == 'NO_DATA'


class TestSensorData:
    """Tests for sensor data endpoint"""
    
    def test_get_latest_sensor_data_success(self, mock_dynamodb, sample_sensor_data):
        """Test successful sensor data retrieval"""
        mock_table = Mock()
        mock_table.query.return_value = {'Items': [sample_sensor_data]}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.get_latest_sensor_data('farm-001')
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['farmId'] == 'farm-001'
        assert body['deviceId'] == 'esp32-abc123'
        assert 'readings' in body
        assert body['readings']['soilMoisture'] == 45.5
    
    def test_get_latest_sensor_data_no_data(self, mock_dynamodb):
        """Test sensor data with no data"""
        mock_table = Mock()
        mock_table.query.return_value = {'Items': []}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.get_latest_sensor_data('farm-999')
        
        assert result['statusCode'] == 404
        body = json.loads(result['body'])
        assert body['error']['code'] == 'NO_DATA'


class TestHistoricalTrends:
    """Tests for historical trends endpoint"""
    
    def test_get_historical_trends_success(self, mock_dynamodb, sample_carbon_calculation):
        """Test successful historical trends retrieval"""
        # Create multiple data points
        items = []
        for i in range(5):
            item = sample_carbon_calculation.copy()
            date = (datetime.utcnow() - timedelta(days=i*30)).isoformat() + 'Z'
            item['calculatedAt'] = date
            items.append(item)
        
        mock_table = Mock()
        mock_table.query.return_value = {'Items': items}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.get_historical_trends('farm-001', 365)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['farmId'] == 'farm-001'
        assert body['days'] == 365
        assert body['dataPoints'] == 5
        assert len(body['trends']) == 5
    
    def test_get_historical_trends_invalid_days(self, mock_dynamodb):
        """Test historical trends with invalid days parameter"""
        result = index.get_historical_trends('farm-001', 500)
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['error']['code'] == 'INVALID_DAYS'
    
    def test_get_historical_trends_no_data(self, mock_dynamodb):
        """Test historical trends with no data"""
        mock_table = Mock()
        mock_table.query.return_value = {'Items': []}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.get_historical_trends('farm-001', 90)
        
        assert result['statusCode'] == 404
        body = json.loads(result['body'])
        assert body['error']['code'] == 'NO_DATA'


class TestCRIWeights:
    """Tests for CRI weights endpoints"""
    
    def test_get_cri_weights_success(self, mock_dynamodb):
        """Test successful CRI weights retrieval"""
        weights_data = {
            'configId': 'default',
            'version': 1,
            'netCarbonPosition': Decimal('0.5'),
            'socTrend': Decimal('0.3'),
            'managementPractices': Decimal('0.2'),
            'updatedAt': datetime.utcnow().isoformat() + 'Z',
            'updatedBy': 'admin-user'
        }
        
        mock_table = Mock()
        mock_table.query.return_value = {'Items': [weights_data]}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.get_cri_weights()
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['configId'] == 'default'
        assert body['weights']['netCarbonPosition'] == 0.5
        assert body['weights']['socTrend'] == 0.3
        assert body['weights']['managementPractices'] == 0.2
    
    def test_get_cri_weights_default(self, mock_dynamodb):
        """Test CRI weights returns defaults when none configured"""
        mock_table = Mock()
        mock_table.query.return_value = {'Items': []}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.get_cri_weights()
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['weights']['netCarbonPosition'] == 0.5
        assert body['weights']['socTrend'] == 0.3
        assert body['weights']['managementPractices'] == 0.2
    
    def test_update_cri_weights_success(self, mock_dynamodb):
        """Test successful CRI weights update by admin"""
        # Mock admin user
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:groups': 'admin',
                        'cognito:username': 'admin-user'
                    }
                }
            }
        }
        
        weights = {
            'netCarbonPosition': 0.6,
            'socTrend': 0.25,
            'managementPractices': 0.15
        }
        
        mock_table = Mock()
        mock_table.query.return_value = {'Items': [{'version': 1}]}
        mock_table.put_item.return_value = {}
        mock_dynamodb.Table.return_value = mock_table
        
        result = index.update_cri_weights(weights, event)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['version'] == 2
        assert body['weights'] == weights
    
    def test_update_cri_weights_unauthorized(self, mock_dynamodb):
        """Test CRI weights update by non-admin user"""
        # Mock non-admin user
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:groups': 'farmer',
                        'cognito:username': 'farmer-user'
                    }
                }
            }
        }
        
        weights = {
            'netCarbonPosition': 0.6,
            'socTrend': 0.25,
            'managementPractices': 0.15
        }
        
        result = index.update_cri_weights(weights, event)
        
        assert result['statusCode'] == 403
        body = json.loads(result['body'])
        assert body['error']['code'] == 'UNAUTHORIZED'
    
    def test_update_cri_weights_invalid_sum(self, mock_dynamodb):
        """Test CRI weights update with invalid sum"""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:groups': 'admin',
                        'cognito:username': 'admin-user'
                    }
                }
            }
        }
        
        weights = {
            'netCarbonPosition': 0.6,
            'socTrend': 0.3,
            'managementPractices': 0.2  # Sum = 1.1, invalid
        }
        
        result = index.update_cri_weights(weights, event)
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['error']['code'] == 'INVALID_WEIGHT_SUM'
    
    def test_update_cri_weights_missing_component(self, mock_dynamodb):
        """Test CRI weights update with missing component"""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:groups': 'admin',
                        'cognito:username': 'admin-user'
                    }
                }
            }
        }
        
        weights = {
            'netCarbonPosition': 0.5,
            'socTrend': 0.5
            # Missing managementPractices
        }
        
        result = index.update_cri_weights(weights, event)
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['error']['code'] == 'INVALID_WEIGHTS'


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_error_response_format(self):
        """Test error response follows standard format"""
        result = index.error_response(404, 'TEST_ERROR', 'Test error message')
        
        assert result['statusCode'] == 404
        body = json.loads(result['body'])
        assert 'error' in body
        assert body['error']['code'] == 'TEST_ERROR'
        assert body['error']['message'] == 'Test error message'
        assert 'timestamp' in body['error']
    
    def test_success_response_format(self):
        """Test success response follows standard format"""
        data = {'test': 'data', 'value': Decimal('123.45')}
        result = index.success_response(data)
        
        assert result['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in result['headers']
        body = json.loads(result['body'])
        assert body['test'] == 'data'
        assert body['value'] == 123.45  # Decimal converted to float


class TestLambdaHandler:
    """Tests for main Lambda handler"""
    
    def test_lambda_handler_routing(self, mock_dynamodb, sample_carbon_calculation):
        """Test Lambda handler routes to correct endpoint"""
        mock_table = Mock()
        mock_table.query.return_value = {'Items': [sample_carbon_calculation]}
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/v1/farms/farm-001/carbon-position',
            'pathParameters': {'farmId': 'farm-001'}
        }
        
        result = index.lambda_handler(event, None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['farmId'] == 'farm-001'
    
    def test_lambda_handler_invalid_endpoint(self):
        """Test Lambda handler with invalid endpoint"""
        event = {
            'httpMethod': 'GET',
            'path': '/api/v1/invalid-endpoint',
            'pathParameters': {}
        }
        
        result = index.lambda_handler(event, None)
        
        assert result['statusCode'] == 404
        body = json.loads(result['body'])
        assert body['error']['code'] == 'ENDPOINT_NOT_FOUND'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
