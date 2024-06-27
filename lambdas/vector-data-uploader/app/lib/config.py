import os
from pathlib import Path

class Config:
    UPLOAD_BUCKET = os.environ.get('VECTOR_DATA_UPLOADER_S3_BUCKET')
    # TODO: This should come from event later on
    UPLOAD_BUCKET_PREFIX = 'shapefile-test/'
    TMP_DIR = Path('/tmp')
