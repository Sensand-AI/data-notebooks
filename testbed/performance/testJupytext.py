import jupytext
import time
import subprocess

# Convert the notebook to a Python script
jupytext.write(jupytext.read('input.ipynb'), 'input_as_script.py')

# Measure execution time of the Python script
start_time = time.time()
subprocess.run(['python', 'input_as_script.py'], check=True)
end_time = time.time()

jupytext_execution_time = end_time - start_time
print(f"Jupytext Execution Time: {jupytext_execution_time} seconds")
