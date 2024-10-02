"""Module to execute a Jupyter notebook with parameters as a Lambda function."""

import datetime
import json
import logging
import os
import shutil
import sys
from typing import Any, Dict

import botocore
import botocore.session
import papermill as pm
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from aws_utils import S3Utils
from botocore.exceptions import BotoCoreError, ClientError
from ddtrace import tracer
from gis_utils.logger import configure_logger
from gis_utils.stac import read_metadata_sidecar
from jsonschema import ValidationError, validate
from papermill.exceptions import PapermillExecutionError

from .constants import AWS_DEFAULT_REGION, AWS_S3_NOTEBOOK_OUTPUT

logger = logging.getLogger("NotebookExecutor")

# Only target the production notebooks directory
notebook_directory = "/var/task/notebooks/production"

client = botocore.session.get_session().create_client("secretsmanager")
cache_config = SecretCacheConfig()
cache = SecretCache(config=cache_config, client=client)

env = os.environ.get("ENV", "False")
is_dev = env != "production"


def get_database_creds():
    # In production, fetch credentials from AWS Secrets Manager
    secret = cache.get_secret_string(
        os.environ.get("DB_CREDENTIALS_SECRET_NAME", "")
    )
    secret_dict = json.loads(secret)

    # Set the secrets as environment variables for future use by Papermill
    os.environ["POSTGRES_DB"] = secret_dict.get("dbname", "")
    os.environ["POSTGRES_USER"] = secret_dict.get("username", "")
    os.environ["POSTGRES_PASSWORD"] = secret_dict.get("password", "")
    os.environ["POSTGRES_HOST"] = os.environ.get("DB_PROXY_ENDPOINT", "")
    os.environ["POSTGRES_PORT"] = str(secret_dict.get("port", 5432))


def init_aws_utils(prefix: str) -> S3Utils:
    """
    Initialize the S3 client.
    By default, the S3Utils class will use the AWS credentials from the environment
    """
    s3_client = S3Utils(
        region_name=AWS_DEFAULT_REGION,
        s3_bucket=AWS_S3_NOTEBOOK_OUTPUT,
        prefix=prefix,
    )
    return s3_client


def validate_schema(event: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validates the incoming event against the provided schema.
    """
    validate(instance=event, schema=schema)


def load_schema(notebook_name: str) -> Dict[str, Any]:
    """
    Each notebook has a corresponding schema.json file that defines the expected parameters.
    Load the JSON Schema for validation
    """
    schema_path = os.path.join(
        notebook_directory, notebook_name, "schema.json"
    )
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        return json.load(schema_file)


def delete_directory(directory_path: str) -> None:
    """
    Deletes the specified directory along with all its contents.

    Parameters:
    - directory_path (str): The path to the directory to be deleted.

    Returns:
    - None
    """

    # Get the absolute path
    abs_directory_path = os.path.abspath(directory_path)

    # Ensure the directory path does not contain a path injection attempt
    if ".." in abs_directory_path:
        logger.error(
            "Directory: path injection attempt detected",
            extra=dict(data={"directory": directory_path}),
        )
        return

    if not os.path.isdir(abs_directory_path):
        logger.error(
            "Directory: does not exist or is not a directory",
            extra=dict(data={"directory": directory_path}),
        )
        return
    if os.path.islink(abs_directory_path):
        logger.error(
            "Directory: is a symbolic link",
            extra=dict(data={"directory": abs_directory_path}),
        )
        return
    try:
        shutil.rmtree(abs_directory_path)
    except FileNotFoundError:
        logger.error(
            "Directory: does not exist",
            extra=dict(data={"directory": abs_directory_path}),
        )
    except PermissionError:
        logger.error(
            "Directory: permission denied",
            extra=dict(data={"directory": abs_directory_path}),
        )
    except OSError as e:
        logger.error(
            "Directory: failed to delete",
            extra=dict(
                data={"directory": abs_directory_path, "error": str(e)}
            ),
        )


@configure_logger(level=logging.INFO)
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

    # If invoked with a function url there's a body key
    if "body" in event:
        event = json.loads(event["body"])

    # If invoked with an SQS event there's a Records key
    # there shoud be only one record as the queue is setup with a batch of 1
    if "Records" in event:
        event = json.loads(event["Records"][0]["body"])

    # Extract notebook name and parameters from the event
    notebook_name = event.get("notebook_name")
    parameters = event.get("parameters", {})
    boundaryId = parameters.get("boundaryId", "unknown")

    if not notebook_name:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": "Missing 'notebook_name' in the event."}
            ),
        }

    # Load the JSON Schema for the specified notebook
    try:
        schema = load_schema(notebook_name)
    except FileNotFoundError:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "File not found."}),
        }

    # Validate the incoming event against the schema
    try:
        validate_schema(event, schema)
    except ValidationError as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": e.message}),
        }

    if not is_dev:
        get_database_creds()

    current_date = datetime.datetime.now()

    # The notebook_key is a deterministic UUID based on the notebook_name and timestamp
    notebook_key = f"{notebook_name}_{current_date.strftime('%Y%m%d%H%M%S')}"
    parameters["notebook_key"] = notebook_key
    save_output = event.get("save_output", True)

    # Create the S3 key for the output notebook based on name and datetime stamp
    notebook_basename = os.path.splitext(notebook_name)[0]
    # Get the base name without extension
    s3_output_key = f"executed_{notebook_basename}_{current_date.strftime('%Y-%m-%d_%H-%M-%S')}.ipynb"
    # Initialize the S3. Don't need to pass credentials if the Lambda has the right IAM role
    # concatenate the notebook name with the notebook key as a prefix and with datetime stamp
    s3_prefix = (
        f"{notebook_name}/{current_date.strftime('%Y-%m-%d')}/{boundaryId}"
    )
    s3_utils = init_aws_utils(prefix=s3_prefix)

    # Define the source and output notebook paths
    # We store our notebooks in the lambda as `notebooks/notebook_name/notebook_name.ipynb`
    notebook_file = f"{notebook_name}.ipynb"
    input_path = os.path.join(notebook_directory, notebook_name, notebook_file)
    output_path = f"/tmp/{s3_output_key}"
    # Create the output directory if it doesn't exist.
    # This is where the notebook generated artifacts will be stored
    output_dir = f"/tmp/{notebook_key}"
    os.makedirs(output_dir, exist_ok=True)

    # Check if the notebook exists
    if not os.path.exists(input_path):
        return {
            "statusCode": 404,
            "body": f'Notebook "{notebook_name}" not found.',
        }

    # Execute the notebook with parameters
    with tracer.trace("execute_notebook", resource=notebook_name):
        try:
            pm.execute_notebook(
                input_path=input_path,
                output_path=output_path,
                parameters=parameters,
                log_output=True,
                progress_bar=False,
                stdout_file=sys.stdout,
                stderr_file=sys.stderr,
            )

            # Read in the generated artifact from the notebook execution.
            # This is a number of files stored in the /tmp/notebook_key directory
            # that we want to upload to S3

            try:
                # List all files in the output directory
                output_files = os.listdir(output_dir)
                bucket_name = AWS_S3_NOTEBOOK_OUTPUT
                uploaded_files = []  # Keep track of successfully uploaded files
                for file in output_files:
                    file_path = os.path.join(output_dir, file)
                    object_key = (
                        f"{s3_prefix}/{file}"  # S3 object key with prefix
                    )
                    # sidecar files don't need to be returned as presigned URLs
                    if file.endswith(".meta.json"):
                        upload_success = s3_utils.upload_file(
                            file_path=file_path
                        )
                        if not upload_success:
                            logger.error(
                                "File upload: Failed to upload metadata file",
                                extra=dict(data={"file": file}),
                            )
                    else:
                        # Read metadata from the sidecar file, if it exists
                        metadata = read_metadata_sidecar(file_path)
                        # Remove the `data` property from the metadata
                        # This is because `data` may contain far too much information to store as S3 metadata
                        file_metadata = (
                            metadata["properties"] if metadata else {}
                        )
                        upload_success = s3_utils.upload_file(
                            file_path=file_path, metadata=file_metadata
                        )

                        if upload_success:
                            # Does the file contain a `.public` before the extension?
                            # If so, we want to generate a pre-signed URL for it
                            if ".public" in file:
                                # Generate a pre-signed URL for the uploaded file
                                logger.info(
                                    "Generating pre-signed URL",
                                    extra=dict(
                                        data={"object_key": object_key}
                                    ),
                                )
                                presigned_url = (
                                    s3_utils.generate_presigned_url(object_key)
                                )

                                uploaded_files.append(
                                    {
                                        "file_name": file,
                                        "presigned_url": presigned_url,
                                        "metadata": metadata,
                                    }
                                )
                            # If the file is not a public file, we just want to return the metadata
                            else:
                                uploaded_files.append(
                                    {
                                        "file_name": file,
                                        "metadata": metadata,
                                    }
                                )

                        else:
                            logger.error(
                                "File upload failed",
                                extra=dict(
                                    data={
                                        "file": file,
                                        "prefix": f"{bucket_name}/{object_key}",
                                    }
                                ),
                            )

                logger.info(
                    "Payload: Response",
                    extra=dict(
                        data={
                            "status": "success",
                            "output_files": uploaded_files,
                        }
                    ),
                )

            except ClientError as e:
                logger.error(
                    "Payload: Executed",
                    extra=dict(
                        data={
                            "status": "error",
                            "notebook_name": notebook_name,
                            "error": str(e),
                        }
                    ),
                )
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(
                        {"message": f"Error uploading file: {e}"}
                    ),
                }
            except FileNotFoundError:
                logger.error("Directory not found: %s", output_dir)
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(
                        {"message": f"Directory not found: {output_dir}"}
                    ),
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

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "message": f"Notebook '{notebook_name}' executed successfully!",
                    "output_files": uploaded_files,
                },
            }

        except (PapermillExecutionError, BotoCoreError) as e:
            logger.error(
                "Payload: Response",
                extra=dict(
                    data={
                        "status": "error",
                        "error": str(e),
                        "notebook_name": notebook_name,
                    }
                ),
            )
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "message": f'Error executing notebook "{notebook_name}": {str(e)}'
                },
            }
