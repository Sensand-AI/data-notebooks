#!/bin/bash

# Install custom python packages in editable mode
# Read the requirements-custom.txt file line by line
# This is because the -e flag is not supported by the requirements.txt file
ls -la
while IFS= read -r line
do
  # If the line starts with './packages', prepend '-e ' to it
  if [[ $line == ./packages* ]]; then
    pip install -e $line
  else
    pip install $line
  fi
done < requirements-custom.txt