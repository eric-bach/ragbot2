#!/usr/bin/env python3
import os

import aws_cdk as cdk

from lib.ragbot2_stack import Ragbot2Stack

app = cdk.App()

# Use CDK's automatic environment detection
# This will use the account/region from your AWS profile
Ragbot2Stack(app, "ragbot-2-stack", env=cdk.Environment(
    account=os.environ.get('CDK_DEFAULT_ACCOUNT'),
    region=os.environ.get('CDK_DEFAULT_REGION')
))

app.synth()
