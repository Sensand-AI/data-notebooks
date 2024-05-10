#!/bin/python
"""
--Function List--
list_tif_files: List all tif files in a directory.

load_settings: Load settings from a JSON file or a file-like object.

arc2meter: Converter arc seconds to meter and vice versa.

meter2arc: Converter arc seconds to meter and vice versa.

get_wcs_capabilities: Get capabilities from WCS layer. Can return some metadata about the dataset as well as individual layers contained in the wcs server.

_getFeatures (internal): Extracts rasterio compatible test from geodataframe.

_read_file: Reads a raster file using rasterio library.

reproj_mask: Masks a raster to the area of a shape, and reprojects.

colour_geotiff_and_save_cog: Colorizes a GeoTIFF image using a specified color map and saves it as a COG (Cloud-Optimized GeoTIFF).

"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import geopandas as gpd
import rioxarray as rxr
import rasterio

from types import SimpleNamespace
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, Resampling
from rasterio.dtypes import uint8
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.plot import reshape_as_raster
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from matplotlib import cm
from matplotlib.colors import Normalize
from owslib.wcs import WebCoverageService


# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


## ------ Setup rasterio profiles ------ ##

class Profile:
    """Base class for Rasterio dataset profiles.

    Subclasses will declare a format driver and driver-specific
    creation options.
    """
    driver = None
    defaults = {}

    def __call__(self, **kwargs):
        """Returns a mapping of keyword args for writing a new datasets.

        Example:

            profile = SomeProfile()
            with rasterio.open('foo.tif', 'w', **profile()) as dst:
                # Write data ...

        """
        if kwargs.get('driver', self.driver) != self.driver:
            raise ValueError(
                "Overriding this profile's driver is not allowed.")
        profile = self.defaults.copy()
        profile.update(**kwargs)
        profile['driver'] = self.driver
        return profile


class DefaultGTiffProfile(Profile):
    """A tiled, band-interleaved, LZW-compressed, 8-bit GTiff profile."""
    driver = 'GTiff'
    defaults = {
        'interleave': 'band',
        'tiled': True,
        'blockxsize': 256,
        'blockysize': 256,
        'compress': 'lzw',
        'nodata': 0,
        'dtype': uint8
    }


default_gtiff_profile = DefaultGTiffProfile()

def list_tif_files(path):
    return [f for f in os.listdir(path) if f.endswith('.tif')]


def load_settings(input_settings):
    """
    Load settings from a JSON file or a file-like object.

    Args:
        input_settings (str or file-like object): The input settings. It can be either a string representing the path to a JSON file or a file-like object containing the JSON data.

    Returns:
        settings (namespace): The loaded settings as a namespace object. The settings can be accessed using dot notation, e.g., `settings.variable_name`.

    Raises:
        ValueError: If the input_settings is neither a string nor a file-like object.

    """
    try:
        if isinstance(input_settings, str):
            with open(input_settings, "r") as f:
                settings = json.load(f)
        else:
            settings = json.load(input_settings)

        settings = SimpleNamespace(**settings)

        settings.date_min = str(settings.date_start)
        settings.date_max = str(settings.date_end)
        return settings
    except Exception as e:
        logger.error(f"Error loading data harvester inputs: {e}")


def calc_arc2meter(arcsec, latitude):
	"""
	Calculate arc seconds to meter

	Input
	-----
	arcsec: float, arcsec
	latitude: float, latitude

	Return
	------
	(meters Long, meters Lat)
	"""
	meter_lng = arcsec * np.cos(latitude * np.pi/180) * 30.922
	meter_lat = arcsec * 30.87
	return (meter_lng, meter_lat)

def calc_meter2arc(meter, latitude):
	"""
	Calculate meter to arc seconds

	Input
	-----
	meter: float, meter
	latitude: float, latitude

	Return
	------
	(arcsec Long, arcsec Lat)
	"""
	arcsec_lng = meter / np.cos(latitude * np.pi/180) / 30.922
	arcsec_lat = meter / 30.87
	return (arcsec_lng, arcsec_lat)


def get_wcs_capabilities(url):
    """
    Get capabilities from WCS layer
    
    NOTE: the url in this case is the 'layers_url' from the json config file. 
    SLGA is different because there are multiple urls, but for DEM and radiometrics, use the single wcs url provided.

    Parameters
    ----------
    url : str
        The URL of the WCS layer.

    Returns
    -------
    keys : list
        A list of layer identifiers.
    titles : list of str
        A list of layer titles.
    descriptions : list of str
        A list of layer descriptions.
    bboxs : list of floats
        A list of layer bounding boxes.
    """

    # Create WCS object
    wcs = WebCoverageService(url, version="1.0.0", timeout=600)
    content = wcs.contents
    keys = content.keys()

    # Get bounding boxes and crs for each coverage
    print("Following data layers are available:")
    bbox_list = []
    title_list = []
    description_list = []
    for key in keys:
        print(f"key: {key}")
        print(f"title: {wcs[key].title}")
        title_list.append(wcs[key].title)
        print(f"{wcs[key].abstract}")
        description_list.append(wcs[key].abstract)
        print(f"bounding box: {wcs[key].boundingboxes}")
        bbox_list.append(wcs[key].boundingboxes)

    return keys, title_list, description_list, bbox_list

def _getFeatures(gdf):
    """
    Internal function to parse features from GeoDataFrame in such a manner that
    rasterio wants them.

    INPUTS
        gdf: geodataframe

    RETURNS
        json object for rasterio to read
    """
    return [json.loads(gdf.to_json())["features"][0]["geometry"]]

def _read_file(file):
    """
    Reads a raster file using rasterio library.

    Args:
        file (str): The path to the raster file.

    Returns:
        numpy.ndarray: The raster data as a NumPy array.

    Raises:
        rasterio.errors.RasterioIOError: If the file cannot be opened or read.

    """
    with rasterio.open(file) as src:
        temp = src.read()
        dims = temp.shape[0]
        if dims == 1:
            return src.read(1)
        else:
            # Returns array in form [channels, long, lat]
            return src.read()


def reproj_mask(filename, input_filepath, bbox, crscode, output_filepath, resample=False):
    """
    Reprojects and masks a raster file based on the given parameters.

    Args:
        filename (str): The name of the input raster file.
        input_filepath (str): The path to the directory containing the input raster file.
        bbox (geopandas.GeoDataFrame): The bounding box geometry used for clipping the raster.
        crscode (str): The CRS code to reproject the raster to.
        output_filepath (str): The path to the directory where the masked raster will be saved.
        resample (bool, optional): Flag indicating whether to perform pixel resampling. Defaults to False.

    Returns:
        xarray.DataArray: The clipped and reprojected raster as a DataArray.

    """
    input_full_filepath = os.path.join(input_filepath, filename)
    masked_filepath = filename.replace(".tif", "_masked.tif")
    mask_outpath = os.path.join(output_filepath, masked_filepath)
    
    try:
        input_raster = rxr.open_rasterio(input_full_filepath)
        
        #run pixel resampling if flag set to true
        if resample is True:
            upscale_factor = 3
            
            # Caluculate new height and width using upscale_factor
            new_width = input_raster.rio.width * upscale_factor
            new_height = input_raster.rio.height * upscale_factor
            
            #upsample raster
            up_sampled = input_raster.rio.reproject(input_raster.rio.crs, shape=(int(new_height), int(new_width)), resampling=Resampling.nearest)
            clipped = up_sampled.rio.clip(bbox.geometry.values)
            clipped.rio.write_nodata(np.nan, inplace=True)
            #clip first as tif and geom need to be in same proejction, and encode the nodata values as nan
            reprojected = clipped.rio.reproject(crscode, nodata=np.nan)
            reprojected.rio.to_raster(mask_outpath, tiled=True)
        else:
            clipped = input_raster.rio.clip(bbox.geometry.values)
            clipped.rio.write_nodata(np.nan, inplace=True)
            #clip first as tif and geom need to be in same proejction, and encode the nodata values as nan
            reprojected = clipped.rio.reproject(crscode, nodata=np.nan)
            reprojected.rio.to_raster(mask_outpath, tiled=True)

        return clipped
    except Exception as e:
        logger.error(f"Error occurred while reprojecting and masking raster: {e}")



# def colour_geotiff_and_save_cog(input_geotiff, colour_map):
#     """
#     Colorizes a GeoTIFF image using a specified color map and saves it as a COG (Cloud-Optimized GeoTIFF).

#     Args:
#         input_geotiff (str): The path to the input GeoTIFF file.
#         colour_map (str): The name of the color map to use for colorizing the image.

#     Raises:
#         Exception: If unable to convert the colored GeoTIFF to a COG.

#     Returns:
#         None
#     """
#     output_colored_tiff_filename = input_geotiff.replace('.tif', '_colored.tif')
#     output_cog_filename = input_geotiff.replace('.tif', '_cog.tif')
#     with rasterio.open(input_geotiff) as src:
#         meta = src.meta.copy()
#         dst_crs = rasterio.crs.CRS.from_epsg(4326) #change so not hardcoded?
#         transform, width, height = calculate_default_transform(
#             src.crs, dst_crs, src.width, src.height, *src.bounds
#         )

#         meta.update({
#             'crs': dst_crs,
#             'transform': transform,
#             'width': width,
#             'height': height
#         })

#         tif_data = src.read(1, masked=True).astype('float32')
#         tif_formatted = tif_data.filled(np.nan)

#         cmap = cm.get_cmap(colour_map)
#         na = tif_formatted[~np.isnan(tif_formatted)]

#         min_value = min(na)
#         max_value = max(na)

#         norm = Normalize(vmin=min_value, vmax=max_value)

#         coloured_data = (cmap(norm(tif_formatted))[:, :, :3] * 255).astype(np.uint8)

#         meta.update({"count":3})


#         with rasterio.open(output_colored_tiff_filename, 'w', **meta) as dst:
#             reshape = reshape_as_raster(coloured_data)
#             dst.write(reshape)

#     try:
#         dst_profile = cog_profiles.get('deflate')
#         with MemoryFile() as mem_dst:
#             cog_translate(
#                 output_colored_tiff_filename,
#                 output_cog_filename,
#                 config=dst_profile,
#                 in_memory=True,
#                 dtype="uint8",
#                 add_mask=False,
#                 nodata=0,
#                 dst_kwargs=dst_profile
#             )
#     except Exception:
#         raise Exception('Unable to convert to cog')
    