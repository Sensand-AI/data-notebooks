import logging
import os
import sys
import json
import numpy as np 
import pystac_client
import rasterio
from rasterio.windows import from_bounds
import rasterio.mask

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


def get_coords_from_geodataframe(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]