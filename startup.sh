#!/bin/bash

# Install the aws_utils package in editable mode
cd /workspaces/data-notebooks/packages/aws_utils
pip install -e .

cd /workspaces/data-notebooks/packages/geodata_utils
pip install -e .


# Start the Flask app in the background
# Assuming your Flask app is located at /workspaces/data-notebooks/api/app.py
cd /workspaces/data-notebooks/api
flask run --host=0.0.0.0 --reload &

# Start Jupyter Notebook server
jupyter notebook --NotebookApp.token='' --NotebookApp.password='' --notebook-dir=/workspaces/data-notebooks/notebooks --port=8888
