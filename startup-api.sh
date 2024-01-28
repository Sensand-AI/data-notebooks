#!/bin/bash

# Install the aws_utils package in editable mode
cd /workspaces/data-notebooks/aws_utils
pip install -e .

# Start Jupyter Kernel Gateway
jupyter kernelgateway --ip=0.0.0.0 --port=8888 --KernelGatewayApp.allow_origin='*' --KernelGatewayApp.api='kernel_gateway.notebook_http' --KernelGatewayApp.seed_uri=${SEED_URI}
