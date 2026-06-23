from aws_cdk import (
    Stack, BundlingOptions, CfnOutput, Duration,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_s3 as s3,
    aws_dynamodb as dynamodb
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, uploads_bucket: s3.IBucket, swings_table: dynamodb.ITable, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        handler_fn = lambda_.Function(
            self,
            "ControlPlaneHandler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.handler",
            code=lambda_.Code.from_asset(
                "src/control_plane",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            timeout=Duration.seconds(15),
            memory_size=256,
        )

        handler_fn.add_environment("SWINGS_TABLE_NAME", swings_table.table_name)
        handler_fn.add_environment("UPLOADS_BUCKET_NAME", uploads_bucket.bucket_name)

        swings_table.grant_read_write_data(handler_fn)
        uploads_bucket.grant_put(handler_fn)

        integration = integrations.HttpLambdaIntegration("ControlPlaneIntegration", handler_fn)
        http_api = apigwv2.HttpApi(self, "ControlPlaneHttpApi", default_integration=integration)

        CfnOutput(self, "ApiEndpoint", value=http_api.api_endpoint)