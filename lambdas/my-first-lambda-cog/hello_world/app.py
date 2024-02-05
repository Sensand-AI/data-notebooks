import os
import subprocess
import sys
import json
import logging

from osgeo import gdal
import rasterio
import pyproj
import shapely
# import requests

# set up logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    length = event['length']
    width = event['width']
    area = calculate_area(length,width)
    print(f"area: {area}")

    logger.info(f"Cloudwatch logs: {context.log_group_name}")

    data = {"area": area}
    return json.dumps(data)

def calculate_area(length, width):
    return length*width