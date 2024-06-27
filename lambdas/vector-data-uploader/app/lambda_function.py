"""Module to execute a Jupyter notebook with parameters as a Lambda function."""

import logging
import os
import shutil

from app.lib.geopandas import find_shapefile, get_gdf
from app.lib.s3 import download_from_prefix
from app.lib.config import Config

# TODO: exception handling
from botocore.exceptions import BotoCoreError, ClientError
from ddtrace import tracer

aws_default_region = os.getenv("AWS_DEFAULT_REGION")
AWS_LAMBDA_FUNCTION_NAME = "vector-data-uploader"

logger = logging.getLogger("VectorDataUploader")
logger.setLevel(logging.INFO)

@tracer.wrap()
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
    except FileNotFoundError:
        logger.error(
            "Directory: does not exist", extra=dict(data={"directory": directory_path})
        )
    except PermissionError:
        logger.error(
            "Directory: permission denied",
            extra=dict(data={"directory": directory_path}),
        )
    except Exception as e:  # This catches other potential exceptions and logs them.
        logger.error(
            "Directory: failed to delete",
            extra=dict(data={"directory": directory_path, "error": str(e)}),
        )


@tracer.wrap()
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

    logger.info("Payload: received", extra=dict(data={"event": event}))
    download_directory = download_from_prefix(Config.UPLOAD_BUCKET_PREFIX)
    shapefile = find_shapefile(download_directory)
    print(shapefile)
    gdf = get_gdf(shapefile)
    logger.info("GeoDataFrame: created", extra=dict(data={"gdf": gdf.head()}))
