"""
Compute Stack - Lambda functions
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iot as iot,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct


class ComputeStack(Stack):
    """Stack for Lambda compute resources"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        sensor_data_table,
        farm_metadata_table,
        carbon_calculations_table,
        ai_model_registry_table,
        sensor_calibration_table,
        cri_weights_table,
        sensor_data_bucket,
        critical_alerts_topic,
        warnings_topic,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Data Ingestion Lambda
        # Processes incoming sensor data from IoT Core
        self.data_ingestion_lambda = lambda_.Function(
            self,
            "DataIngestionLambda",
            function_name="carbonready-data-ingestion",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("lambda/data_ingestion"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "SENSOR_DATA_TABLE": sensor_data_table.table_name,
                "SENSOR_CALIBRATION_TABLE": sensor_calibration_table.table_name,
                "SENSOR_DATA_BUCKET": sensor_data_bucket.bucket_name,
                "CRITICAL_ALERTS_TOPIC": critical_alerts_topic.topic_arn,
                "WARNINGS_TOPIC": warnings_topic.topic_arn,
            },
        )

        # Grant permissions to Data Ingestion Lambda
        sensor_data_table.grant_write_data(self.data_ingestion_lambda)
        sensor_calibration_table.grant_read_data(self.data_ingestion_lambda)
        sensor_data_bucket.grant_write(self.data_ingestion_lambda)
        critical_alerts_topic.grant_publish(self.data_ingestion_lambda)
        warnings_topic.grant_publish(self.data_ingestion_lambda)

        # IoT Rule to trigger Data Ingestion Lambda
        # Routes sensor data messages to Lambda
        iot_rule_role = iam.Role(
            self,
            "IoTRuleRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
        )
        self.data_ingestion_lambda.grant_invoke(iot_rule_role)

        self.sensor_data_rule = iot.CfnTopicRule(
            self,
            "SensorDataRule",
            rule_name="CarbonReadySensorDataRule",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM 'carbonready/farm/+/sensor/data' WHERE EXISTS(hash)",
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        lambda_=iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=self.data_ingestion_lambda.function_arn
                        )
                    )
                ],
                rule_disabled=False,
                aws_iot_sql_version="2016-03-23",
            ),
        )

        # AI Processing Lambda
        # Performs carbon calculations on a scheduled basis
        self.ai_processing_lambda = lambda_.Function(
            self,
            "AIProcessingLambda",
            function_name="carbonready-ai-processing",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("lambda/ai_processing"),
            timeout=Duration.minutes(5),
            memory_size=2048,
            environment={
                "FARM_METADATA_TABLE": farm_metadata_table.table_name,
                "CARBON_CALCULATIONS_TABLE": carbon_calculations_table.table_name,
                "AI_MODEL_REGISTRY_TABLE": ai_model_registry_table.table_name,
                "CRI_WEIGHTS_TABLE": cri_weights_table.table_name,
                "SENSOR_DATA_TABLE": sensor_data_table.table_name,
            },
        )

        # Grant permissions to AI Processing Lambda
        farm_metadata_table.grant_read_data(self.ai_processing_lambda)
        carbon_calculations_table.grant_read_write_data(self.ai_processing_lambda)
        ai_model_registry_table.grant_read_data(self.ai_processing_lambda)
        cri_weights_table.grant_read_data(self.ai_processing_lambda)
        sensor_data_table.grant_read_data(self.ai_processing_lambda)

        # EventBridge rule to trigger AI Processing Lambda daily at 02:00 UTC
        ai_processing_rule = events.Rule(
            self,
            "AIProcessingSchedule",
            schedule=events.Schedule.cron(minute="0", hour="2"),
            description="Trigger AI processing pipeline daily at 02:00 UTC",
        )
        ai_processing_rule.add_target(
            targets.LambdaFunction(self.ai_processing_lambda)
        )
