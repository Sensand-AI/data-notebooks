#!/bin/bash

# Execute your Python script
python testPapermillAndJupytext.py > "results_$(date +%Y-%m-%d_%H-%M-%S).txt"

# Find and remove __pycache__ directories in the project folder
#find . -type d -name "__pycache__" -exec rm -r {} +

echo "Python script executed and __pycache__ directories cleared."