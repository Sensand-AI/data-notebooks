import datetime
import os

import boto3
import papermill as pm
from datadog import initialize, statsd
from ddtrace import tracer

initialize(statsd_host=os.environ.get('DATADOG_HOST'))
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = 'us-east-1'

@tracer.wrap(name='lambda_handler', service='notebook-executor')
def lambda_handler(event, context):
    
    # Extract notebook name and parameters from the event
    notebook_name = event.get('notebook_name')
    parameters = event.get('parameters', {})
    save_output = event.get('save_output', True)
    s3_bucket = 'jenna-remote-sensing-sandbox' # S3 bucket to save the output notebook

    # Generate a datetime stamp
    datetime_stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Dynamically create the S3 key for the output notebook to include the proper extension and a datetime stamp
    notebook_basename = os.path.splitext(notebook_name)[0]  # Get the base name without extension
    s3_output_key = f'executed_{notebook_basename}_{datetime_stamp}.ipynb'  # Append datetime stamp and '.ipynb'

    # Initialize the S3 client. Don't need to pass the credentials if the Lambda has the right IAM role
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

    # Define the source and output notebook paths
    input_path = os.path.join('/var/task/notebooks', notebook_name)
    output_path = '/tmp/executed_notebookzz.ipynb'

    # Check if the notebook exists
    if not os.path.exists(input_path):
        statsd.increment('notebook.execution.notebook_not_found')
        return {
            'statusCode': 404,
            'body': f'Notebook "{notebook_name}" not found.'
        }

    # Execute the notebook with parameters
    with tracer.trace("execute_notebook", resource=notebook_name):
        try:
            pm.execute_notebook(input_path, output_path, parameters=parameters)

            # If enabled, save the executed notebook to S3
            s3.upload_file(output_path, s3_bucket, s3_output_key)

            statsd.increment('notebook.execution.success')
            return {
                'statusCode': 200,
                'body': f'Notebook "{notebook_name}" executed successfully!'
            }
        except Exception as e:
            statsd.increment('notebook.execution.error')
            return {
                'statusCode': 500,
                'body': f'Error executing notebook "{notebook_name}": {str(e)}'
            }
