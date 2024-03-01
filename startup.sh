#!/bin/bash

# Install custom packages in editable mode
pip install -r /workspaces/data-notebooks/requirements-custom.txt

# Start Jupyter Notebook server
jupyter notebook --ip=0.0.0.0 --NotebookApp.token='' --NotebookApp.password='' --notebook-dir=/workspaces/data-notebooks/notebooks --port=8888 --allow-root