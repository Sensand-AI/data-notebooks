import os
from pathlib import Path

SUCCESS_PREFIX = 'shapefile-test/'
DBF_MISSING_PREFIX = 'dbf-missing/'
PRJ_MISSING_PREFIX = 'prj-missing/'

class Config:
    UPLOAD_BUCKET = os.environ.get('VECTOR_DATA_UPLOADER_S3_BUCKET')
    # TODO: This should come from event later on
    UPLOAD_BUCKET_PREFIX = DBF_MISSING_PREFIX
    TMP_DIR = Path('/tmp')
