#!/usr/bin/env python3
"""
CarbonReady AWS CDK Application
Main entry point for infrastructure deployment
"""
import aws_cdk as cdk
from cdk.stacks.iot_stack import IoTStack
from cdk.stacks.data_stack import DataStack
from cdk.stacks.compute_stack import ComputeStack
from cdk.stacks.api_stack import ApiStack
from cdk.stacks.monitoring_stack import MonitoringStack

app = cdk.App()

# Environment configuration
env = cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region") or "ap-south-1"  # Mumbai region for Goa
)

# Data stack - DynamoDB tables and S3 buckets
data_stack = DataStack(app, "CarbonReadyDataStack", env=env)

# IoT stack - AWS IoT Core configuration
iot_stack = IoTStack(app, "CarbonReadyIoTStack", env=env)

# Monitoring stack - CloudWatch and SNS
monitoring_stack = MonitoringStack(app, "CarbonReadyMonitoringStack", env=env)

# Compute stack - Lambda functions
compute_stack = ComputeStack(
    app, 
    "CarbonReadyComputeStack",
    sensor_data_table=data_stack.sensor_data_table,
    farm_metadata_table=data_stack.farm_metadata_table,
    carbon_calculations_table=data_stack.carbon_calculations_table,
    ai_model_registry_table=data_stack.ai_model_registry_table,
    sensor_calibration_table=data_stack.sensor_calibration_table,
    cri_weights_table=data_stack.cri_weights_table,
    sensor_data_bucket=data_stack.sensor_data_bucket,
    critical_alerts_topic=monitoring_stack.critical_alerts_topic,
    warnings_topic=monitoring_stack.warnings_topic,
    env=env
)

# API stack - API Gateway and Cognito
api_stack = ApiStack(
    app,
    "CarbonReadyApiStack",
    farm_metadata_table=data_stack.farm_metadata_table,
    carbon_calculations_table=data_stack.carbon_calculations_table,
    sensor_data_table=data_stack.sensor_data_table,
    cri_weights_table=data_stack.cri_weights_table,
    env=env
)

# Add dependencies
compute_stack.add_dependency(data_stack)
compute_stack.add_dependency(monitoring_stack)
api_stack.add_dependency(data_stack)

app.synth()
