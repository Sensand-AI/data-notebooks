#!/bin/bash

# Install custom packages in editable mode
pip install -r /workspaces/data-notebooks/requirements-custom.txt

# Start Jupyter Kernel Gateway
jupyter kernelgateway --ip=0.0.0.0 --port=8888 --KernelGatewayApp.allow_origin='*' --KernelGatewayApp.api='kernel_gateway.notebook_http' --KernelGatewayApp.seed_uri=${SEED_URI}
