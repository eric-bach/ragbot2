#!/usr/bin/env python3
import os
import aws_cdk as cdk
from lib.data_stack import DataStack
from lib.app_stack import AppStack

app = cdk.App()

APP_NAME = 'ragbot2'
ENV_NAME = os.environ.get('ENV_NAME', 'dev')  # Read from environment or default to 'dev'

dataProps = DataStack(app, f"{APP_NAME}-data", 
    app_name=APP_NAME,
    env_name=ENV_NAME,
    env=cdk.Environment(
        account=os.environ.get('CDK_DEFAULT_ACCOUNT'),
        region=os.environ.get('CDK_DEFAULT_REGION')
    )
)

AppStack(app, f"{APP_NAME}-app", 
    app_name=APP_NAME,
    env_name=ENV_NAME,
    data_resources=dataProps.resources,
    env=cdk.Environment(
        account=os.environ.get('CDK_DEFAULT_ACCOUNT'),
        region=os.environ.get('CDK_DEFAULT_REGION')
    )
)

app.synth()
