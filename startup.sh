#!/bin/bash

# Install the aws_utils package in editable mode
cd /workspaces/data-notebooks/aws_utils
pip install -e .

# Start Jupyter Notebook server
jupyter notebook --NotebookApp.token='' --NotebookApp.password='' --notebook-dir=/workspaces/data-notebooks/notebooks