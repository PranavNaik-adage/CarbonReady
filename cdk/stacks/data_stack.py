"""
Data Stack - DynamoDB tables and S3 buckets
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
)
from constructs import Construct


class DataStack(Stack):
    """Stack for data storage resources"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table: SensorData
        # Stores sensor readings with 90-day TTL
        self.sensor_data_table = dynamodb.Table(
            self,
            "SensorDataTable",
            partition_key=dynamodb.Attribute(
                name="farmId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # GSI for querying by deviceId
        self.sensor_data_table.add_global_secondary_index(
            index_name="deviceId-timestamp-index",
            partition_key=dynamodb.Attribute(
                name="deviceId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.NUMBER
            ),
        )

        # DynamoDB Table: FarmMetadata
        # Stores farm information with versioning
        self.farm_metadata_table = dynamodb.Table(
            self,
            "FarmMetadataTable",
            partition_key=dynamodb.Attribute(
                name="farmId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB Table: CarbonCalculations
        # Stores carbon calculation results with 10-year retention
        self.carbon_calculations_table = dynamodb.Table(
            self,
            "CarbonCalculationsTable",
            partition_key=dynamodb.Attribute(
                name="farmId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="calculatedAt", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB Table: AIModelRegistry
        # Stores AI model versions with 10-year retention
        self.ai_model_registry_table = dynamodb.Table(
            self,
            "AIModelRegistryTable",
            partition_key=dynamodb.Attribute(
                name="modelType", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB Table: SensorCalibration
        # Stores sensor calibration events
        self.sensor_calibration_table = dynamodb.Table(
            self,
            "SensorCalibrationTable",
            partition_key=dynamodb.Attribute(
                name="deviceId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="calibrationDate", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB Table: CRIWeights
        # Stores Carbon Readiness Index weighting configuration
        self.cri_weights_table = dynamodb.Table(
            self,
            "CRIWeightsTable",
            partition_key=dynamodb.Attribute(
                name="configId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB Table: GrowthCurves
        # Stores regional growth curve parameters for sequestration estimation
        self.growth_curves_table = dynamodb.Table(
            self,
            "GrowthCurvesTable",
            partition_key=dynamodb.Attribute(
                name="cropType", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="region", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # S3 Bucket: Sensor Data Storage
        # Stores raw and processed sensor data with lifecycle policies
        self.sensor_data_bucket = s3.Bucket(
            self,
            "SensorDataBucket",
            bucket_name=None,  # Auto-generate unique name
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                # Archive raw data to Glacier after 1 year
                s3.LifecycleRule(
                    id="ArchiveRawDataToGlacier",
                    enabled=True,
                    prefix="raw/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365),
                        )
                    ],
                ),
                # Archive processed data to Glacier after 1 year
                s3.LifecycleRule(
                    id="ArchiveProcessedDataToGlacier",
                    enabled=True,
                    prefix="processed/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365),
                        )
                    ],
                ),
            ],
        )
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table: SensorData
        # Stores sensor readings with 90-day TTL
        self.sensor_data_table = dynamodb.Table(
            self,
            "SensorDataTable",
            partition_key=dynamodb.Attribute(
                name="farmId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # GSI for querying by deviceId
        self.sensor_data_table.add_global_secondary_index(
            index_name="deviceId-timestamp-index",
            partition_key=dynamodb.Attribute(
                name="deviceId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.NUMBER
            ),
        )

        # DynamoDB Table: FarmMetadata
        # Stores farm information with versioning
        self.farm_metadata_table = dynamodb.Table(
            self,
            "FarmMetadataTable",
            partition_key=dynamodb.Attribute(
                name="farmId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB Table: CarbonCalculations
        # Stores carbon calculation results with 10-year retention
        self.carbon_calculations_table = dynamodb.Table(
            self,
            "CarbonCalculationsTable",
            partition_key=dynamodb.Attribute(
                name="farmId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="calculatedAt", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB Table: AIModelRegistry
        # Stores AI model versions with 10-year retention
        self.ai_model_registry_table = dynamodb.Table(
            self,
            "AIModelRegistryTable",
            partition_key=dynamodb.Attribute(
                name="modelType", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB Table: SensorCalibration
        # Stores sensor calibration events
        self.sensor_calibration_table = dynamodb.Table(
            self,
            "SensorCalibrationTable",
            partition_key=dynamodb.Attribute(
                name="deviceId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="calibrationDate", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB Table: CRIWeights
        # Stores Carbon Readiness Index weighting configuration
        self.cri_weights_table = dynamodb.Table(
            self,
            "CRIWeightsTable",
            partition_key=dynamodb.Attribute(
                name="configId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # DynamoDB Table: GrowthCurves
        # Stores regional growth curve parameters for sequestration estimation
        self.growth_curves_table = dynamodb.Table(
            self,
            "GrowthCurvesTable",
            partition_key=dynamodb.Attribute(
                name="cropType", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="region", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # S3 Bucket: Sensor Data Storage
        # Stores raw and processed sensor data with lifecycle policies
        self.sensor_data_bucket = s3.Bucket(
            self,
            "SensorDataBucket",
            bucket_name=None,  # Auto-generate unique name
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                # Archive raw data to Glacier after 1 year
                s3.LifecycleRule(
                    id="ArchiveRawDataToGlacier",
                    enabled=True,
                    prefix="raw/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365),
                        )
                    ],
                ),
                # Archive processed data to Glacier after 1 year
                s3.LifecycleRule(
                    id="ArchiveProcessedDataToGlacier",
                    enabled=True,
                    prefix="processed/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365),
                        )
                    ],
                ),
            ],
        )

