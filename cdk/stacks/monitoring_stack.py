"""
Monitoring Stack - CloudWatch and SNS
"""
from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_logs as logs,
)
from constructs import Construct


class MonitoringStack(Stack):
    """Stack for monitoring and alerting resources"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SNS Topic: Critical Alerts
        # For Lambda failures, data tampering, authentication failures
        self.critical_alerts_topic = sns.Topic(
            self,
            "CriticalAlertsTopic",
            topic_name="carbonready-critical-alerts",
            display_name="CarbonReady Critical Alerts",
        )

        # SNS Topic: Warnings
        # For calibration expiry, data validation errors
        self.warnings_topic = sns.Topic(
            self,
            "WarningsTopic",
            topic_name="carbonready-warnings",
            display_name="CarbonReady Warnings",
        )

        # CloudWatch Log Groups will be created automatically by Lambda functions
        # but we can define retention policies here

        # Log Group for Data Ingestion Lambda
        self.data_ingestion_log_group = logs.LogGroup(
            self,
            "DataIngestionLogGroup",
            log_group_name="/aws/lambda/carbonready-data-ingestion",
            retention=logs.RetentionDays.ONE_YEAR,
        )

        # Log Group for AI Processing Lambda
        self.ai_processing_log_group = logs.LogGroup(
            self,
            "AIProcessingLogGroup",
            log_group_name="/aws/lambda/carbonready-ai-processing",
            retention=logs.RetentionDays.ONE_YEAR,
        )

        # Log Group for Dashboard API Lambda
        self.dashboard_api_log_group = logs.LogGroup(
            self,
            "DashboardAPILogGroup",
            log_group_name="/aws/lambda/carbonready-dashboard-api",
            retention=logs.RetentionDays.ONE_YEAR,
        )

        # Log Group for Farm Metadata API Lambda
        self.farm_metadata_api_log_group = logs.LogGroup(
            self,
            "FarmMetadataAPILogGroup",
            log_group_name="/aws/lambda/carbonready-farm-metadata-api",
            retention=logs.RetentionDays.ONE_YEAR,
        )
