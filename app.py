#!/usr/bin/env python3
import os
import aws_cdk as cdk

from infrastructure.data_stack import DataStack
from infrastructure.api_stack import ApiStack
from infrastructure.deployment_stack import DeploymentStack

app = cdk.App()

data_stack = DataStack(app, "DataStack",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)

ApiStack(app, "ApiStack",
    uploads_bucket=data_stack.uploads_bucket,
    swings_table=data_stack.swings_table,
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)

DeploymentStack(app, "DeploymentStack", env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
