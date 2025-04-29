#!/usr/bin/env python3
from cdk_nag import AwsSolutionsChecks

import aws_cdk as cdk
from stacks.kb_stack import DataFoundationStack
from stacks.lambda_stack import LambdaStack
from stacks.bedrock_stack import BedrockStack
from stacks.streamlit_stack import StreamlitStack

app = cdk.App()

dict1 = {"region": os.environ["AWS_REGION"], "account_id": os.environ["AWS_ACCOUNT_ID"]}

stack1 = DataFoundationStack(
    app,
    "DataStack",
    env=cdk.Environment(account=dict1["account_id"], region=dict1["region"]),
    description="Data lake and processing resources",
    termination_protection=False,
    tags={"project": "genai-prototype"},
)

stack2 = LambdaStack(
    app,
    "LambdaStack",
    env=cdk.Environment(account=dict1["account_id"], region=dict1["region"]),
    description="Lambda resources for the bedrock action groups",
    termination_protection=False,
    tags={"project": "genai-prototype"},
    dict1=dict1,
)

stack3 = BedrockStack(
    app,
    "BedrockAgentStack",
    env=cdk.Environment(account=dict1["account_id"], region=dict1["region"]),
    description="Bedrock agent resources",
    termination_protection=False,
    tags={"project": "genai-prototype"},
    dict1=dict1,
    athena_lambda_arn=stack2.athena_lambda_arn,
    search_lambda_arn=stack2.search_lambda_arn,
)

stack4 = StreamlitStack(
    app,
    "StreamlitStack",
    env=cdk.Environment(account=dict1["account_id"], region=dict1["region"]),
    description="Streamlit app resources",
    termination_protection=False,
    tags={"project": "genai-prototype"},
    dict1=dict1,
)

stack2.add_dependency(stack1)
stack3.add_dependency(stack2)
stack4.add_dependency(stack3)

cdk.Tags.of(stack1).add(key="owner", value="ccoe")
cdk.Tags.of(stack2).add(key="owner", value="ccoe")
cdk.Tags.of(stack3).add(key="owner", value="ccoe")
cdk.Tags.of(stack4).add(key="owner", value="ccoe")

cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=False))
app.synth()
