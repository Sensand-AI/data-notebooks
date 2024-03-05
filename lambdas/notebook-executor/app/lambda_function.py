"""Module to execute a Jupyter notebook with parameters as a Lambda function."""

import datetime
import os
import json
from typing import Any, Dict
import boto3
import papermill as pm
from datadog import initialize, statsd
from ddtrace import tracer

from jsonschema import validate, ValidationError

from papermill.exceptions import PapermillExecutionError
from botocore.exceptions import BotoCoreError

initialize(statsd_host=os.environ.get('DATADOG_HOST'))
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION_NAME = 'us-east-1'

@tracer.wrap(name='validate_event', service='notebook-executor')
def validate_event(event: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validates the incoming event against the provided schema."""
    validate(instance=event, schema=schema)

@tracer.wrap(name='load_schema', service='notebook-executor')
def load_schema(notebook_name: str):
    """Load the JSON Schema for validating the notebook parameters."""
    schema_path = os.path.join('/var/task/notebooks', notebook_name, 'schema.json')
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as schema_file:
            return json.load(schema_file)
    else:
        raise FileNotFoundError(f"Schema file for notebook {notebook_name} not found.")

@tracer.wrap(name='lambda_handler', service='notebook-executor')
def lambda_handler(event, _):
    """
    Handles a Lambda event.

    This function is the entry point for AWS Lambda. It is called
    whenever the Lambda function is triggered.

    Args:
        event (dict): AWS Lambda uses this parameter to pass in event data to the handler.
        _ (LambdaContext): AWS Lambda uses this to provide runtime information to the handler.

    Returns:
        dict: The output of the Lambda function. Must be JSON serializable.
    """

    # Extract notebook name and parameters from the event
    notebook_name = event.get('notebook_name')

    if not notebook_name:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': 'Missing "notebook_name" in the event.'
        }

    # Load the JSON Schema for the specified notebook
    try:
        schema = load_schema(notebook_name)
    except FileNotFoundError as e:
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': str(e)
        }

    # Validate the incoming event against the schema
    try:
        validate_event(event, schema)
    except ValidationError as e:
        return {
            'statusCode': 400, 
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }

    parameters = event.get('parameters', {})
    save_output = event.get('save_output', True)
    s3_bucket = 'jenna-remote-sensing-sandbox' # S3 bucket to save the output notebook

    # Generate a datetime stamp
    datetime_stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Create the S3 key for the output notebook based on name and datetime stamp
    notebook_basename = os.path.splitext(notebook_name)[0]  # Get the base name without extension
    s3_output_key = f'executed_{notebook_basename}_{datetime_stamp}.ipynb'
    # Initialize the S3. Don't need to pass credentials if the Lambda has the right IAM role
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=REGION_NAME
    )

    # Define the source and output notebook paths
    # We store our notebooks in the lambda as `notebooks/notebook_name/notebook_name.ipynb`
    notebook_file = notebook_name + '.ipynb'
    input_path = os.path.join('/var/task/notebooks', notebook_name, notebook_file)
    output_path = f'/tmp/executed_{notebook_name}_{datetime_stamp}.ipynb'

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
            if save_output:
                s3.upload_file(output_path, s3_bucket, s3_output_key)

            statsd.increment('notebook.execution.success')
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': f'Notebook "{notebook_name}" executed successfully!'
            }
        except (PapermillExecutionError, BotoCoreError) as e:
            statsd.increment('notebook.execution.error')
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': f'Error executing notebook "{notebook_name}": {str(e)}'
            }
