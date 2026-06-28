from aws_cdk import CfnOutput, Stack, DefaultStackSynthesizer
from aws_cdk.aws_iam import OpenIdConnectProvider, Role, OpenIdConnectPrincipal, PolicyStatement
from constructs import Construct

token_url = "token.actions.githubusercontent.com"
client_id = "sts.amazonaws.com"


class DeploymentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        provider = OpenIdConnectProvider(
            self, "GithubActionsDeployProvider",
            url=f"https://{token_url}",
            client_ids=[client_id]
        )

        role = Role(
            self, "GithubActionsDeployRole",
            assumed_by=OpenIdConnectPrincipal(
                provider,
                conditions={
                    "StringEquals": {
                        f"{token_url}:aud": client_id,
                    },
                    "StringLike": {
                        f"{token_url}:sub": "repo:aroberts91/fix-my-swing-backend:*"
                    }
                }
            )
        )

        role.add_to_policy(PolicyStatement(
            actions=["sts:AssumeRole"],
            resources=[f"arn:aws:iam::{self.account}:role/cdk-{DefaultStackSynthesizer.DEFAULT_QUALIFIER}-*"]
        ))

        CfnOutput(self, "GithubActionsDeployRoleArn", value=role.role_arn)