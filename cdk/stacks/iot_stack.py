"""
IoT Stack - AWS IoT Core configuration
"""
from aws_cdk import (
    Stack,
    aws_iot as iot,
)
from constructs import Construct


class IoTStack(Stack):
    """Stack for AWS IoT Core resources"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # IoT Policy for ESP32 sensors
        # Allows devices to connect, publish to their farm topic, and subscribe to commands
        self.sensor_policy = iot.CfnPolicy(
            self,
            "ESP32SensorPolicy",
            policy_name="CarbonReadyESP32SensorPolicy",
            policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["iot:Connect"],
                        "Resource": [
                            f"arn:aws:iot:{self.region}:{self.account}:client/${{iot:Connection.Thing.ThingName}}"
                        ],
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["iot:Publish"],
                        "Resource": [
                            f"arn:aws:iot:{self.region}:{self.account}:topic/carbonready/farm/${{iot:Connection.Thing.Attributes[farmId]}}/sensor/data"
                        ],
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["iot:Subscribe"],
                        "Resource": [
                            f"arn:aws:iot:{self.region}:{self.account}:topicfilter/carbonready/farm/${{iot:Connection.Thing.Attributes[farmId]}}/commands"
                        ],
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["iot:Receive"],
                        "Resource": [
                            f"arn:aws:iot:{self.region}:{self.account}:topic/carbonready/farm/${{iot:Connection.Thing.Attributes[farmId]}}/commands"
                        ],
                    },
                ],
            },
        )

        # Note: IoT Rule will be created in compute_stack.py since it needs Lambda function reference
        # Thing Groups and individual Things (devices) will be provisioned during device setup
