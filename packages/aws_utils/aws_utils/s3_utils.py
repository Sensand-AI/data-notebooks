import os
import functools
import boto3
from botocore.exceptions import ClientError

def use_default_bucket(func):
    """A decorator to set the default bucket for S3 operations."""
    @functools.wraps(func)
    def wrapper(self, *args, bucket=None, **kwargs):
        if bucket is None:
            bucket = self.default_bucket
        return func(self, *args, bucket=bucket, **kwargs)
    return wrapper

class S3Utils:
    """Class to interact with AWS S3."""

    def __init__(
        self,
        aws_access_key_id,
        aws_secret_access_key,
        region_name,
        s3_bucket=None,
        **kwargs
    ):
        """
        Initialize the S3 client.

        :param aws_access_key_id: AWS access key ID.
        :param aws_secret_access_key: AWS secret access key.
        :param region_name: AWS region name.
        :param s3_bucket: Default S3 bucket name to use.
        :param kwargs: Additional arguments to pass to the boto client.
            e.g. endpoint_url, aws_session_token, etc.
        """
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            **kwargs

        )
        self.default_bucket = s3_bucket if s3_bucket else None

    @use_default_bucket
    def list_files(self, bucket, prefix):
        """
        List files in an S3 bucket.
        """
        file_keys = []
        try:
            # Use the paginator because the list could be very large
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for item in page.get('Contents', []):
                    file_keys.append(item['Key'])
        except ClientError as e:
            print(f"An error occurred: {e}")
            raise e
        return file_keys

    @use_default_bucket
    def upload_file(self, file_path, bucket, file_name=None, prefix=None):
        """
        Upload a file to a specific prefix in an S3 bucket.
        """
        try:
            # Use the provided file_name or fallback to the name from the file_path
            if not file_name:
                file_name = os.path.basename(file_path)

            full_key = f"{prefix}/{file_name}" if prefix else file_name

            # Open and read the file in binary mode
            with open(file_path, 'rb') as file_data:
                self.s3_client.put_object(Bucket=bucket, Key=full_key, Body=file_data)

            return f"File '{file_name}' uploaded successfully to '{full_key}' in bucket '{bucket}'."

        except ClientError as e:
            return f"An error occurred: {e}"

    @use_default_bucket
    def get_file(self, file_name, bucket, prefix):
        """
        Get a file from a specific prefix in an S3 bucket.
        """
        try:
            object_key = f"{prefix}{file_name}"
            response = self.s3_client.get_object(Bucket=bucket, Key=object_key)
            return response['Body'].read()
        except ClientError as e:
            return f"An error occurred: {e}"

    @use_default_bucket
    def generate_presigned_url(self, bucket, object_key, expiration=60):
        """
        Generate a presigned URL to share an S3 object.
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            return f"An error occurred: {e}"

    @use_default_bucket
    def generate_presigned_urls(self, prefix, expiration=60, bucket=None):
        """
        Generate presigned URLs for all files within a specific prefix in the bucket.

        :param prefix: The prefix (folder path) to list files under.
        :param expiration: The expiration time in seconds for the presigned URLs.
        :param bucket: The bucket from which to list files. Uses the default bucket if None.
        :return: A dictionary with file keys as keys and their presigned URLs as values.
        """
        presigned_urls = {}

        try:
            # Retrieve a list of all file keys under the specified prefix
            file_keys = self.list_files(prefix=prefix, bucket=bucket)

            # Generate a presigned URL for each file
            for file_key in file_keys:
                presigned_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': file_key},
                    ExpiresIn=expiration
                )
                presigned_urls[file_key] = presigned_url

            return presigned_urls
        except ClientError as e:
            print(f"An error occurred: {e}")
            raise e