import os
import papermill as pm

def lambda_handler(event, context):
    # Extract notebook name and parameters from the event
    notebook_name = event.get('notebook_name')
    parameters = event.get('parameters', {})
    save_output = event.get('save_output', False)

    # Define the source and output notebook paths
    input_path = os.path.join('/var/task/notebooks', notebook_name)
    output_path = os.path.join('/var/task/notebooks', f'executed_{notebook_name}') if save_output else '/dev/null'

    # Check if the notebook exists
    if not os.path.exists(input_path):
        return {
            'statusCode': 404,
            'body': f'Notebook "{notebook_name}" not found.'
        }

    # Execute the notebook with parameters
    try:
        pm.execute_notebook(input_path, output_path, parameters=parameters)
        return {
            'statusCode': 200,
            'body': f'Notebook "{notebook_name}" executed successfully!'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error executing notebook "{notebook_name}": {str(e)}'
        }
