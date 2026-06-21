#!/usr/bin/env python3
import os
import aws_cdk as cdk

from infrastructure.data_stack import DataStack

app = cdk.App()

DataStack(app, "DataStack",
          env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
      )

app.synth()
