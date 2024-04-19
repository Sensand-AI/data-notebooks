"""Module to execute a Jupyter notebook with parameters as a Lambda function."""
import datetime
import json
import logging
import os
import shutil
import sys
import uuid
from typing import Any, Dict

import papermill as pm
from aws_utils import S3Utils
from botocore.exceptions import BotoCoreError, ClientError
from ddtrace import tracer
from gis_utils.stac import read_metadata_sidecar
from jsonschema import ValidationError, validate
from papermill.exceptions import PapermillExecutionError

# from datadog_lambda.metric import lambda_metric

# initialize(statsd_host=os.environ.get('DATADOG_HOST'))
aws_s3_notebook_output = os.getenv('AWS_S3_BUCKET_NOTEBOOK_OUTPUT')
aws_default_region = os.getenv('AWS_DEFAULT_REGION')
AWS_LAMBDA_FUNCTION_NAME = 'notebook-executor'

# Configure logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

@tracer.wrap(name='init_aws_utils', service=AWS_LAMBDA_FUNCTION_NAME)
def init_aws_utils(prefix):
    """
    Initialize the S3 client.
    By default, the S3Utils class will use the AWS credentials from the environment
    """
    s3_client = S3Utils(
        region_name=aws_default_region,
        s3_bucket=aws_s3_notebook_output,
        prefix=prefix
    )
    return s3_client

@tracer.wrap(name='generate_deterministic_uuid', service=AWS_LAMBDA_FUNCTION_NAME)
def generate_deterministic_uuid(notebook_name: str, parameters: dict):
    """
    Generates a deterministic UUID using the Lambda function name and AWS 
    region as part of the namespace, and the notebook name and parameters as the name.
    """
    # Use AWS Lambda function name and AWS region as part of the namespace
    namespace_uuid = uuid.uuid5(
        uuid.NAMESPACE_DNS,
        f"{AWS_LAMBDA_FUNCTION_NAME}-{aws_default_region}"
    )

    # Remove parameters that are not deterministic
    parameters_to_unset = ['geojson']
    settable_parameters = []
    for param in parameters_to_unset:
        if param not in parameters:
            settable_parameters.append(param)

    # Generate a UUID based on the notebook name and a stringified, sorted version of parameters
    sorted_parameters = json.dumps(settable_parameters, sort_keys=True)
    name_string = f"{notebook_name}-{sorted_parameters}"
    deterministic_uuid = uuid.uuid5(namespace_uuid, name_string)

    return str(deterministic_uuid)

@tracer.wrap()
def validate_event(event: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validates the incoming event against the provided schema."""
    validate(instance=event, schema=schema)

@tracer.wrap(name='load_schema', service=AWS_LAMBDA_FUNCTION_NAME)
def load_schema(notebook_name: str):
    """Load the JSON Schema for validating the notebook parameters."""
    schema_path = os.path.join('/var/task/notebooks', notebook_name, 'schema.json')
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as schema_file:
            return json.load(schema_file)
    else:
        raise FileNotFoundError(f"Schema file for notebook {notebook_name} not found.")

def delete_directory(directory_path):
    """
    Deletes the specified directory along with all its contents.

    Parameters:
    - directory_path (str): The path to the directory to be deleted.

    Returns:
    - None
    """
    try:
        shutil.rmtree(directory_path)
        print(f"Successfully deleted the directory: {directory_path}")
    except FileNotFoundError:
        print(f"The directory {directory_path} does not exist.")
    except PermissionError:
        print(f"Permission denied: unable to delete some or all of the contents of {directory_path}")
    except Exception as e:  # This catches other potential exceptions and logs them.
        print(f"An error occurred: {e}")

@tracer.wrap(name='lambda_handler', service=AWS_LAMBDA_FUNCTION_NAME)
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
            'body': json.dumps({'error': e.message})
        }

    parameters = event.get('parameters', {})
    # Append a deterministic UUID to the parameters as a notebook_key
    # This will be used to identify the executed notebook in the S3 bucket
    # and later to retrieve the output
    # It will also be used as a means of tracking executions when we eventually
    # handle retries and error handling via a persistent store
    notebook_key = generate_deterministic_uuid(notebook_name, parameters)
    print(f"Generated notebook key: {notebook_key}")
    parameters['notebook_key'] = notebook_key
    save_output = event.get('save_output', True)

    # Generate a datetime stamp
    datetime_stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Create the S3 key for the output notebook based on name and datetime stamp
    notebook_basename = os.path.splitext(notebook_name)[0]  # Get the base name without extension
    s3_output_key = f'executed_{notebook_basename}_{datetime_stamp}.ipynb'
    # Initialize the S3. Don't need to pass credentials if the Lambda has the right IAM role
    s3_utils = init_aws_utils(prefix=notebook_key)
    # s3_client = boto3.client('s3')
    print(f"Output will be saved to bucket: {aws_s3_notebook_output}")
    print(f"Output will be saved to region: {aws_default_region}")

    # Define the source and output notebook paths
    # We store our notebooks in the lambda as `notebooks/notebook_name/notebook_name.ipynb`
    notebook_file = notebook_name + '.ipynb'
    input_path = os.path.join('/var/task/notebooks', notebook_name, notebook_file)
    output_path = f'/tmp/{s3_output_key}.ipynb'
    # Create the output directory if it doesn't exist. 
    # This is where the notebook generated artifacts will be stored
    output_dir = f"/tmp/{notebook_key}"
    os.makedirs(output_dir, exist_ok=True)

    # Check if the notebook exists
    if not os.path.exists(input_path):
        # lambda_metric(
        #     metric_name='notebook.execution.notebook_not_found',
        #     value=1
        # )
        return {
            'statusCode': 404,
            'body': f'Notebook "{notebook_name}" not found.'
        }

    # Execute the notebook with parameters
    with tracer.trace("execute_notebook", resource=notebook_name):
        try:
            pm.execute_notebook(
                input_path=input_path,
                output_path=output_path,
                parameters=parameters,
                log_output=True,
                stdout_file=sys.stdout,
                stderr_file=sys.stderr,
            )

            print(f"Notebook '{notebook_name}' executed successfully!")

            # Read in the generated artifact from the notebook execution.
            # This is a number of files stored in the /tmp/notebook_key directory
            # that we want to upload to S3

            try:
                # List all files in the output directory
                output_files = os.listdir(output_dir)
                bucket_name = aws_s3_notebook_output
                uploaded_files = []  # Keep track of successfully uploaded files
                for file in output_files:
                    file_path = os.path.join(output_dir, file)
                    object_key = f"{notebook_key}/{file}"  # S3 object key with prefix
                    print(f"Uploading file {file} to {bucket_name}/{object_key}")
                    # sidecar files don't need to be returned as presigned URLs
                    if file.endswith(".meta.json"):
                        print(f"File path: {file_path}")
                        upload_success = s3_utils.upload_file(file_path=file_path)
                        if not upload_success:
                            print(f"Failed to upload metadata file {file} to {bucket_name}/{object_key}")
                    else:
                        # Read metadata from the sidecar file, if it exists
                        metadata = read_metadata_sidecar(file_path)
                        # Remove the `data` property from the metadata
                        # This is because `data` may contain far too much information to store as S3 metadata
                        file_metadata = metadata['properties'] if metadata else {}
                        upload_success = s3_utils.upload_file(file_path=file_path, metadata=file_metadata)

                        if upload_success:
                            print(f"File {file} uploaded successfully to {bucket_name}/{object_key}")

                            # Does the file contain a `.public` before the extension?
                            # If so, we want to generate a pre-signed URL for it
                            if ".public" in file:
                                print(f"Generating pre-signed URL for {file}")
                                # Generate a pre-signed URL for the uploaded file
                                presigned_url = s3_utils.generate_presigned_url(object_key)
                                print(f"Pre-signed URL generated: {presigned_url}")

                                uploaded_files.append({
                                    'file_name': file,
                                    'presigned_url': presigned_url,
                                    'metadata': metadata
                                })

                        else:
                            print(f"Failed to upload file {file} to {bucket_name}/{object_key}")

                # Check if all files were uploaded successfully
                # if len(uploaded_files) == len(output_files):
                #     # All files uploaded, proceed to generate pre-signed URLs for each file
                #     presigned_urls = [s3_utils.generate_presigned_url(object_key) for object_key in uploaded_files]
                #     print("Pre-signed URLs generated successfully.")

            except ClientError as e:
                logger.error(e)
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'message': f"Error uploading file: {e}"
                    })
                }
            except FileNotFoundError:
                logger.error(f"Directory not found: {output_dir}")
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'message': f"Directory not found: {output_dir}"
                    })
                }

            # Delete the temporary directory
            # Some of the files may be large and we don't want to keep them around
            # And the lambda may be reused for another execution soon
            delete_directory(output_dir)

            # If enabled, save the executed notebook to S3
            if save_output:
                s3_utils.upload_file(
                    file_path=output_path,
                )

            print(uploaded_files)

            # statsd.increment('notebook.execution.success')

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': {
                    'message': f"Notebook '{notebook_name}' executed successfully!",
                    "output_files": uploaded_files
                }
            }

            # return {
            #     'statusCode': 200,
            #     'headers': {
            #         'Content-Type': 'application/json'
            #     },
            #     'body': {
            #         "message": f"Notebook '{notebook_name}' executed successfully!",
            #         "output_type": output_type,
            #         "output_files": [s3_utils.generate_presigned_urls(prefix=notebook_key)]
            #     }
            # }
        except (PapermillExecutionError, BotoCoreError) as e:
            # statsd.increment('notebook.execution.error')
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': {
                    'message': f'Error executing notebook "{notebook_name}": {str(e)}'
                }
            }
