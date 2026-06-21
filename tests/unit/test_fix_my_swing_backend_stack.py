import aws_cdk as core
import aws_cdk.assertions as assertions

from fix_my_swing_backend.fix_my_swing_backend_stack import FixMySwingBackendStack

# example tests. To run these tests, uncomment this file along with the example
# resource in fix_my_swing_backend/fix_my_swing_backend_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = FixMySwingBackendStack(app, "fix-my-swing-backend")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
