#!/usr/bin/env python3
import os

import aws_cdk as cdk

from lib.ragbot2_stack import Ragbot2Stack

app = cdk.App()

Ragbot2Stack(app, "ragbot-2-stack")

app.synth()
