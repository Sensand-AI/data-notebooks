#!/bin/bash

# Start Jupyter Notebook server
jupyter notebook --ip=0.0.0.0 --NotebookApp.token='vscode' --NotebookApp.password='' --notebook-dir=/var/task/notebooks --port=8888 --allow-root --NotebookApp.ip='0.0.0.0' --NotebookApp.allow_origin='*'