import os

import boto3
from botocore.exceptions import ClientError

class S3Utils:
    """Class to interact with AWS S3."""

    def __init__(
        self,
        aws_access_key_id,
        aws_secret_access_key,
        region_name, s3_bucket,
        endpoint_url=None
    ):
        """
        Initialize the S3 client.

        :param aws_access_key_id: AWS access key ID.
        :param aws_secret_access_key: AWS secret access key.
        :param region_name: AWS region name.
        :param s3_bucket: Default S3 bucket name to use.
        :param endpoint_url: Custom endpoint URL, if any (e.g., for local development using s3mock).
        """
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            endpoint_url=endpoint_url
        )
        self.default_bucket = s3_bucket

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

    def generate_presigned_url(self, bucket_name, object_key, expiration=60):
        """
        Generate a presigned URL to share an S3 object.
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            return f"An error occurred: {e}"
        