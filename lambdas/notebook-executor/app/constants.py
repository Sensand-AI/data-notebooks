import os

AWS_S3_NOTEBOOK_OUTPUT = os.getenv("AWS_S3_BUCKET_NOTEBOOK_OUTPUT")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

AWS_LAMBDA_FUNCTION_NAME = "notebook-executor"
NOTEBOOK_DIRECTORY = "/var/task/notebooks/production"
