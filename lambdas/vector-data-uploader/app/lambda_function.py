"""Module to execute a Jupyter notebook with parameters as a Lambda function."""

import logging
import os
import shutil
import botocore
import signal
import json
import sys
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig 
from sqlalchemy import create_engine


from app.lib.geopandas import find_shapefile, get_gdf, write_to_postgis
from app.lib.s3 import download_from_prefix
from app.lib.config import Config

# TODO: exception handling
from botocore.exceptions import BotoCoreError, ClientError
from ddtrace import tracer

aws_default_region = os.getenv("AWS_DEFAULT_REGION")
AWS_LAMBDA_FUNCTION_NAME = "vector-data-uploader"

is_dev = os.environ.get("IS_DEV", "False") == "True"

ENGINE = None

def close_db():
    global ENGINE
    if ENGINE is not None:
        logger.info('gracefully disconnecting db')
        ENGINE.dispose()
    sys.exit(0)

signal.signal(signal.SIGINT, lambda: close_db(ENGINE))

client = botocore.session.get_session().create_client('secretsmanager')
cache_config = SecretCacheConfig()
cache = SecretCache( config = cache_config, client = client)

def init_db():
    global ENGINE

    if is_dev:
        dbname=os.environ.get("POSTGRES_ENGINE", "")
        user=os.environ.get("POSTGRES_USER", "")
        password=os.environ.get("POSTGRES_PASSWORD", "")
        host=os.environ.get("POSTGRES_HOST", "")
        port=os.environ.get("POSTGRES_PORT", "")
    else:
        secret = cache.get_secret_string(os.environ.get("VECTOR_DATA_UPLOADER_DB_CREDENTIALS_SECRET_NAME", ""))
        secret_dict = json.loads(secret)

        dbname=secret_dict.get('dbname')
        user=secret_dict.get('username')
        password=secret_dict.get('password')
        host=os.environ.get("VECOTOR_DATA_UPLOADER_ENGINE_PROXY_ENDPOINT", "")
        port=secret_dict.get('port', 5432)


    if ENGINE is None:
        logger.info(f"Connecting to db {dbname} as {user} on {host}:{port}")
        ENGINE = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{dbname}")

# Configure logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("VectorDataUploader")
logger.setLevel(logging.INFO)

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

@tracer.wrap(name='lambda_handler')
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
    init_db()
    download_directory = download_from_prefix(Config.UPLOAD_BUCKET_PREFIX)
    shapefile = find_shapefile(download_directory)
    if shapefile is None:
        logger.error("Shapefile: not found", extra=dict(data={"directory": download_directory}))
        delete_directory(download_directory)
        return {"statusCode": 404, "body": json.dumps({"message": "Shapefile not found"})}

    gdf = get_gdf(shapefile)
    logger.info("GeoDataFrame: created", extra=dict(data={"gdf": gdf.head()}))
    write_to_postgis(gdf, ENGINE)
    logger.info("GeoDataFrame: written to DB")
    delete_directory(download_directory)
