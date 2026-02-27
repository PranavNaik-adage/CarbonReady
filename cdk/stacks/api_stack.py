"""
API Stack - API Gateway and Cognito
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
)
from constructs import Construct


class ApiStack(Stack):
    """Stack for API Gateway and authentication resources"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        farm_metadata_table,
        carbon_calculations_table,
        sensor_data_table,
        cri_weights_table,
        critical_alerts_topic,
        warnings_topic,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cognito User Pool for authentication
        self.user_pool = cognito.UserPool(
            self,
            "CarbonReadyUserPool",
            user_pool_name="carbonready-users",
            self_sign_up_enabled=False,  # Admin-managed user creation
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True)
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
        )

        # Create user groups for role-based access control
        farmer_group = cognito.CfnUserPoolGroup(
            self,
            "FarmerGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="farmer",
            description="Farmer role - can view their own farm data",
        )

        admin_group = cognito.CfnUserPoolGroup(
            self,
            "AdminGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="admin",
            description="Admin role - can modify CRI weights and view all data",
        )

        # Cognito User Pool Client
        self.user_pool_client = self.user_pool.add_client(
            "CarbonReadyUserPoolClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            generate_secret=False,
        )

        # Farm Metadata API Lambda
        self.farm_metadata_lambda = lambda_.Function(
            self,
            "FarmMetadataAPILambda",
            function_name="carbonready-farm-metadata-api",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("lambda/farm_metadata_api"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "FARM_METADATA_TABLE": farm_metadata_table.table_name,
                "CRITICAL_ALERTS_TOPIC": critical_alerts_topic.topic_arn,
                "WARNINGS_TOPIC": warnings_topic.topic_arn,
            },
        )

        # Grant permissions
        farm_metadata_table.grant_read_write_data(self.farm_metadata_lambda)
        critical_alerts_topic.grant_publish(self.farm_metadata_lambda)
        warnings_topic.grant_publish(self.farm_metadata_lambda)

        # Dashboard API Lambda
        self.dashboard_api_lambda = lambda_.Function(
            self,
            "DashboardAPILambda",
            function_name="carbonready-dashboard-api",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("lambda/dashboard_api"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "CARBON_CALCULATIONS_TABLE": carbon_calculations_table.table_name,
                "SENSOR_DATA_TABLE": sensor_data_table.table_name,
                "CRI_WEIGHTS_TABLE": cri_weights_table.table_name,
                "CRITICAL_ALERTS_TOPIC": critical_alerts_topic.topic_arn,
                "WARNINGS_TOPIC": warnings_topic.topic_arn,
            },
        )

        # Grant permissions
        carbon_calculations_table.grant_read_data(self.dashboard_api_lambda)
        sensor_data_table.grant_read_data(self.dashboard_api_lambda)
        cri_weights_table.grant_read_write_data(self.dashboard_api_lambda)
        critical_alerts_topic.grant_publish(self.dashboard_api_lambda)
        warnings_topic.grant_publish(self.dashboard_api_lambda)

        # API Gateway with Cognito authorizer
        self.api = apigateway.RestApi(
            self,
            "CarbonReadyAPI",
            rest_api_name="CarbonReady API",
            description="API for CarbonReady carbon intelligence platform",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=['Content-Type', 'Authorization'],
            ),
        )

        # Cognito authorizer with JWT token validation
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            "CarbonReadyAuthorizer",
            cognito_user_pools=[self.user_pool],
            authorizer_name="CarbonReadyJWTAuthorizer",
            identity_source="method.request.header.Authorization",
        )

        # API v1 resource
        api_v1 = self.api.root.add_resource("api").add_resource("v1")

        # Farm metadata endpoints
        farms = api_v1.add_resource("farms")
        farm = farms.add_resource("{farmId}")
        metadata = farm.add_resource("metadata")

        metadata.add_method(
            "GET",
            apigateway.LambdaIntegration(self.farm_metadata_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )
        metadata.add_method(
            "POST",
            apigateway.LambdaIntegration(self.farm_metadata_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )
        metadata.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.farm_metadata_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # Dashboard endpoints - all require authentication
        carbon_position = farm.add_resource("carbon-position")
        carbon_position.add_method(
            "GET",
            apigateway.LambdaIntegration(self.dashboard_api_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        cri = farm.add_resource("carbon-readiness-index")
        cri.add_method(
            "GET",
            apigateway.LambdaIntegration(self.dashboard_api_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        sensor_data = farm.add_resource("sensor-data").add_resource("latest")
        sensor_data.add_method(
            "GET",
            apigateway.LambdaIntegration(self.dashboard_api_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        historical_trends = farm.add_resource("historical-trends")
        historical_trends.add_method(
            "GET",
            apigateway.LambdaIntegration(self.dashboard_api_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # Admin endpoints for CRI weights - require authentication
        # Authorization check (admin role) is done in Lambda function
        admin = api_v1.add_resource("admin")
        cri_weights = admin.add_resource("cri-weights")
        cri_weights.add_method(
            "GET",
            apigateway.LambdaIntegration(self.dashboard_api_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )
        cri_weights.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.dashboard_api_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )
