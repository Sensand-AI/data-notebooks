import functools
import logging
import os
import sys

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

def use_default_prefix(func):
    """A decorator to set the default prefix for S3 operations."""
    @functools.wraps(func)
    def wrapper(self, *args, prefix=None, **kwargs):
        if prefix is None:
            prefix = self.prefix
        return func(self, *args, prefix=prefix, **kwargs)
    return wrapper

class S3Utils:
    """Class to interact with AWS S3."""

    def __init__(
        self,
        region_name=None,
        s3_bucket=None,
        prefix=None,
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
            region_name=region_name,
            **kwargs
        )
        self.default_bucket = s3_bucket if s3_bucket else None
        self.prefix = prefix if prefix else None

    @use_default_bucket
    @use_default_prefix
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
                    file = {}
                    file['file_name'] = page.get('Name', 'unknown')
                    file['prefix'] = page.get('Prefix', 'unknown')
                    file['key'] = item['Key']
                    file_keys.append(file)
        except ClientError as e:
            print(f"An error occurred: {e}")
            raise e
        return file_keys

    @use_default_bucket
    @use_default_prefix
    def upload_file(self, file_path, bucket=None, prefix=None, file_name=None, metadata=None):
        """
        Upload a file to a specific prefix in an S3 bucket.
        """
        try:
            # Use the provided file_name or fallback to the name from the file_path
            if not file_name:
                file_name = os.path.basename(file_path)
                print(f"uploading file_name: {file_name} and file_path: {file_path}")

            full_key = f"{prefix}/{file_name}" if prefix else file_name

            # Open and read the file in binary mode
            with open(file_path, 'rb') as file_data:
                self.s3_client.put_object(
                    Bucket=bucket, 
                    Key=full_key, 
                    Body=file_data,
                    Metadata=metadata if metadata else {}
                )

            print(f"File {file_name} uploaded successfully.")
            return True

        except ClientError as e:
            print(f"An error occurred: {e}")
            raise e

    def upload_folder(self, folder_path, ignored_extensions, bucket=None, prefix=None):
        """
        Uploads the contents of a folder to S3, preserving the directory structure.
        """
        if ignored_extensions is None:
            ignored_extensions = []  # Default to an empty list if none provided

        # Convert ignored_extensions to lowercase for case insensitive comparison
        ignored_extensions = [ext.lower() for ext in ignored_extensions]
        # Add specific filenames to ignore
        ignored_filenames = {".ds_store"}

        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                # Skip specific filenames
                if filename.lower() in ignored_filenames:
                    continue  # Skip the upload of ignored files

                # Extract the file extension and convert to lowercase
                extension = os.path.splitext(filename)[1].lower()
                if extension in ignored_extensions:
                    continue  # Skip the upload of files with ignored extensions

                file_path = os.path.join(root, filename)
                # Compute the relative path to maintain directory structure on S3
                relative_path = os.path.relpath(file_path, start=folder_path)
                # Create the full S3 key for the file
                s3_key = os.path.join(prefix, relative_path).replace('\\', '/') if prefix else relative_path.replace('\\', '/')
                try:
                    # Upload the file
                    self.upload_file(file_path=file_path, bucket=bucket, prefix='', file_name=s3_key)
                    print(f"Successfully uploaded {s3_key} to S3 bucket {bucket}")
                except ClientError as e:
                    print(f"Failed to upload {s3_key} to S3 bucket {bucket}. AWS ClientError: {e}")
                    continue  # Optionally continue to try uploading the next files
                except Exception as e:
                    print(f"An unexpected error occurred while uploading {s3_key}: {e}")
                    continue  # Optionally continue to try uploading the next files



    @use_default_bucket
    @use_default_prefix
    def get_file(self, file_name, bucket=None, prefix=None):
        """
        Get a file from a specific prefix in an S3 bucket.
        """
        try:
            object_key = f"{prefix}/{file_name}"
            response = self.s3_client.get_object(Bucket=bucket, Key=object_key)
            return response['Body'].read()
        except ClientError as e:
            return f"An error occurred: {e}"

    @use_default_bucket
    @use_default_prefix
    def generate_presigned_url(self, file_name, bucket=None, prefix=None, expiration=3600):
        """
        Generate a presigned URL to share an S3 object.
        """
        try:
            object_key = f"{prefix}/{file_name}"
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': file_name
                },
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            return f"An error occurred: {e}"

    @use_default_bucket
    @use_default_prefix
    def generate_presigned_urls(self, bucket=None, prefix=None, expiration=3600):
        """
        Generate presigned URLs for all files within a specific prefix in the bucket.
        """
        presigned_urls = {}  # Initialize `presigned_urls` as a dictionary

        try:
            file_keys = self.list_files(prefix=prefix, bucket=bucket)

            for file_key in file_keys:
                presigned_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': file_key['key']},
                    ExpiresIn=expiration
                )
                presigned_urls[file_key['file_name']] = presigned_url  # Correct usage as a dictionary

            return presigned_urls
        except ClientError as e:
            print(f"An error occurred: {e}")
            raise e