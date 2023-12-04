import boto3

class AwsS3Functions:
    def __init__(self, aws_access_key_id, aws_secret_access_key):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

    def list_files(self, bucket, prefix):
        """
        List files in an S3 bucket.
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            return [item['Key'] for item in response.get('Contents', [])]
        except Exception as e:
            return f"An error occurred: {e}"

    def upload_file(self, file_name, data, bucket, prefix):
        """
        Upload a file to a specific prefix in an S3 bucket.
        """
        try:
            object_key = f"{prefix}{file_name}"
            self.s3_client.put_object(Bucket=bucket, Key=object_key, Body=data)
            return f"File '{file_name}' uploaded successfully to '{prefix}' in bucket '{bucket}'"
        except Exception as e:
            return f"An error occurred: {e}"

    def get_file(self, file_name, bucket, prefix):
        """
        Get a file from a specific prefix in an S3 bucket.
        """
        try:
            object_key = f"{prefix}{file_name}"
            response = self.s3_client.get_object(Bucket=bucket, Key=object_key)
            return response['Body'].read()
        except Exception as e:
            return f"An error occurred: {e}"
