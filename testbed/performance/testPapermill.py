import time
import papermill as pm

start_time = time.time()
pm.execute_notebook(
    'input.ipynb',
    'output_papermill.ipynb'
)
end_time = time.time()

papermill_execution_time = end_time - start_time
print(f"Papermill Execution Time: {papermill_execution_time} seconds")
