import os
import papermill as pm

def lambda_handler(event, context):
    # Extract notebook name and parameters from the event
    notebook_name = event.get('notebook_name')
    parameters = event.get('parameters', {})

    # Define the source and output notebook paths
    input_path = os.path.join('/var/task/notebooks', notebook_name)
    output_path = os.path.join('/var/task/notebooks', f'executed_{notebook_name}')

    # Execute the notebook with parameters
    pm.execute_notebook(input_path, output_path, parameters=parameters)

    return {
        'statusCode': 200,
        'body': f'Notebook {notebook_name} executed successfully!'
    }
