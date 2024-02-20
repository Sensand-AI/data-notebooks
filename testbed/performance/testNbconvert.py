import time
import subprocess

start_time = time.time()
subprocess.run(['jupyter', 'nbconvert', '--to', 'notebook', '--execute',
                '--output', 'output_notebook_nbconvert.ipynb', 'input_notebook.ipynb'], check=True)
end_time = time.time()

nbconvert_execution_time = end_time - start_time
print(f"nbconvert Execution Time: {nbconvert_execution_time} seconds")
