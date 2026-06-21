from aws_cdk import (
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    Stack
)

from constructs import Construct

class DataStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.uploads_bucket = s3.Bucket(
            self,
            "UploadsBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            cors=[
                s3.CorsRule(
                    allowed_origins=["http://localhost:3000"],
                    allowed_methods=[s3.HttpMethods.PUT],
                    allowed_headers=["*"],
                )
            ],
            event_bridge_enabled=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.swings_table = dynamodb.Table(
            self,
            "SwingsTable",
            partition_key=dynamodb.Attribute(
                name="swingId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="expiresAt"
        )