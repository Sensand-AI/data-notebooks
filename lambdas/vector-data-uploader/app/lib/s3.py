import boto3
import os
from app.lib.config import Config

client = boto3.client('s3')
resource = boto3.resource('s3')

def download_from_prefix(prefix: str, bucket=Config.UPLOAD_BUCKET):
    local = Config.TMP_DIR / prefix
    if not os.path.exists(local):
        os.makedirs(local)

    paginator = client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=prefix):
        for file in result.get('Contents', []):
            file_name = file.get('Key').split('/')[-1]
            dest_pathname = os.path.join(local, file_name)
            if not file.get('Key', '').endswith('/'):
                print(f"Downloading {file.get('Key')} to {dest_pathname}")
                resource.meta.client.download_file(bucket, file.get('Key'), dest_pathname)

    return local
