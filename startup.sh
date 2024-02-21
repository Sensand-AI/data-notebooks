#!/bin/bash

# Install custom packages in editable mode
pip install -r /workspaces/data-notebooks/requirements-custom.txt

# Start the Flask app in the background
# Assuming your Flask app is located at /workspaces/data-notebooks/api/app.py
cd /workspaces/data-notebooks/api
flask run --host=0.0.0.0 --reload &

# Start Jupyter Notebook server
jupyter notebook --NotebookApp.token='' --NotebookApp.password='' --notebook-dir=/workspaces/data-notebooks/notebooks --port=8888
