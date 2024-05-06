#!/bin/python
"""
Utility functions for use in the Agrefed data harvesting pipeline.

--Function List--

arc2meter: Converter arc seconds to meter and vice versa.

meter2arc: Converter arc seconds to meter and vice versa.

get_wcs_capabilities: Get capabilities from WCS layer. Can return some metadata about the dataset as well as individual layers contained in the wcs server.

_getFeatures (internal): Extracts rasterio compatible test from geodataframe.

reproj_mask: Masks a raster to the area of a shape, and reprojects.

reproj_rastermatch: Reproject a file to match the shape and projection of
    existing raster.
    
reproj_raster: Reproject and clip for a given output resolution, crs and bbox.

_read_file (internal): Reads raster with rasterio returns numpy array

aggregate_rasters: Averages (or similar) over multiple files and multiple
    channels.
    
aggregate_multiband: Averages (or similar) over multiple files but keeps
    multi-channels independent.
    
_get_coords_at_point (internal): Finds closest index of a point-location in an
    array (raster).
    
raster_query: Given a longitude,latitude value, return the value at that point
    of a raster/tif.
    
extract_values_from_rasters: Given a list of rasters, extract the values at coords.

"""

import os
import sys
import json
import logging
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import rioxarray as rxr
import rasterio
import matplotlib.pyplot as plt

from types import SimpleNamespace
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.plot import show
from rasterio.dtypes import uint8
from rasterio.enums import Resampling #for spatial resampling of pixels
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.plot import reshape_as_raster

from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

from matplotlib import cm
from matplotlib.colors import Normalize

from shapely.geometry import box #try and remove later
from owslib.wcs import WebCoverageService
from pyproj import CRS
from pathlib import Path
from numba import jit
from glob import glob
from alive_progress import alive_bar, config_handler

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

config_handler.set_global(
    force_tty=True,
    bar=None,
    spinner="waves",
    monitor=False,
    stats=False,
    receipt=True,
    elapsed="{elapsed}",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    filename="harvest.txt",
    filemode="w",
)

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

## ------ Functions to show progress and provide feedback to the user ------ ##

def spin(message=None, events=1, log=False):
    """Spin animation as a progress inidicator"""
    if log:
        logging.info(message)
    return alive_bar(events, title=message)


def msg_info(message, icon=False, log=False):
    """Prints an info message"""
    if log:
        logging.info(message)
    if icon:
        print(message)
    else:
        print(message)


def msg_dl(message, log=False):
    """Prints a downloading message"""
    if log:
        logging.info(message)
    print(message)


def msg_warn(message, log=False):
    """Prints a warning message"""
    if log:
        logging.warning(message)
    print(message)


def msg_err(message, log=False):
    """Prints an error message"""
    if log:
        logging.error(message)
    print(message)


def msg_success(message, log=False):
    """Prints a success message"""
    if log:
        logging.info(message)
    print(message)


## ------------------------------------------------------------------------- ##

def list_tif_files(path):
    return [f for f in os.listdir(path) if f.endswith('.tif')]

def load_settings(input_settings):
    # Check if the input is a string (path) or a file-like object
    if isinstance(input_settings, str):
        # If string, open the file as usual
        with open(input_settings, "r") as f:
            settings = json.load(f)
    else:
        # If file-like object, load directly without opening a file
        settings = json.load(input_settings)
        
    # Parse settings dictinary as namespace (settings are available as
    # settings.variable_name rather than settings['variable_name'])
    settings = SimpleNamespace(**settings)
    
    settings.date_min = str(settings.date_start)
    settings.date_max = str(settings.date_end)
    return settings

"""
Converter arc seconds to meter and vice versa.

Earth circumference around Equator is 40,075,017 meter
1 arc second at equatorial sea level = 1855.325m/60 = 30.922m

Earth circumference around Poles is 40,007,863 meter
1 arc second latitude = 1852.216m/60 = 30.87m

Formula for longitude: meters = arcsec * cos(degree latitude) * 30.922m
(conversion for latitude stays constant: arcsec * 30.87m)
"""

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
    
    NOTE: the url in this case is the 'layers_url' from the json config file. SLGA is different because there are multiple urls, but for DEM and radiometrics, use the single wcs url provided.

    Parameters
    ----------
    url : str
        layer url

    Returns
    -------
    keys    : list
        layer identifiers
    titles  : list  of str
        layer titles
    descriptions : list of str
        layer descriptions
    bboxs   : list of floats
        layer bounding boxes
    """

    # Create WCS object
    wcs = WebCoverageService(url, version="1.0.0",timeout=600)
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
        print("")

    return keys, title_list, description_list, bbox_list
## ------------------------------------------------------------------------- ##

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
    Internal function to read a raster file with rasterio

    INPUT:
        file: filepath to raster file

    RETURNS:
        Either single data array or multi-dimensional array if input is multiband.
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
    Clips a raster to the area of a shape, and reprojects. Also tiles the output geotif so it is cloud-optimised.

    INPUTS
        filepath: input filename
        input_filepath: directory with harvested, unmasked source data
        bbox: geometry(polygon) defining mask boundary
        crscode: optional, coordinate reference system as defined by EPSG
        filepath_out: directory for saved masked geotifs to be placed
     """
    input_full_filepath = os.path.join(input_filepath, filename)
    masked_filepath = filename.replace(".tif", "_masked.tif")
    mask_outpath = os.path.join(output_filepath, masked_filepath)
    
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
        reprojected = clipped.rio.reproject(crscode, nodata=np.nan) #clip first as tif and geom need to be in same proejction, and encode the nodata values as nan
        reprojected.rio.to_raster(mask_outpath, tiled=True)
    else:
        clipped = input_raster.rio.clip(bbox.geometry.values)
        clipped.rio.write_nodata(np.nan, inplace=True)
        reprojected = clipped.rio.reproject(crscode, nodata=np.nan) #clip first as tif and geom need to be in same proejction, and encode the nodata values as nan
        reprojected.rio.to_raster(mask_outpath, tiled=True)

    return clipped

def reproj_rastermatch(filename, input_filepath, match_filename, match_filepath, output_filename, output_filepath, nodata):
    """
    Reproject a file to match the shape and projection of existing raster.
    Output file is written to disk.

    Parameters
    ----------
    infile : (string) path to input file to reproject
    matchfile : (string) path to raster with desired shape and projection
    outfile : (string) path to output file tif
    nodata : (float) nodata value for output raster
    """
    infile = os.path.join(input_filepath, filename)
    matchfile = os.path.join(match_filepath, match_filename)
    outfile = os.path.join(output_filepath, output_filename)
    
    with rasterio.open(infile) as src:
        src_transform = src.transform

        # open input to match
        with rasterio.open(matchfile) as match:
            dst_crs = match.crs

            # calculate the output transform matrix
            dst_transform, dst_width, dst_height = calculate_default_transform(
                src.crs,  # input CRS
                dst_crs,  # output CRS
                match.width,  # input width
                match.height,  # input height
                *match.bounds,  # unpacks input outer boundaries (left, bottom, right, top)
            )

        # set properties for output
        dst_kwargs = src.meta.copy()
        dst_kwargs.update(
            {
                "crs": dst_crs,
                "transform": dst_transform,
                "width": dst_width,
                "height": dst_height,
                "nodata": nodata,
            }
        )
        # print("Coregistered to shape:", dst_height, dst_width, "\n Affine", dst_transform)
        
        # open output
        with rasterio.open(outfile, "w", **dst_kwargs) as dst:
            # iterate through bands and write using reproject function
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest,
                )


def aggregate_rasters(
    file_list=None, data_dir=None, agg=["mean"], outfile="aggregation"
):
    """
    Aggregrates over multiple files and over all channels
    and writes results to new tif file(s).

    Parameters
    ----------
    file_list : list of strings
        List of files to aggregate
    data_dir : string
        Path to directory containing files
    agg : list of strings
        List of aggregation methods to apply (mean, median, sum, perc95, perc5)
    outfile : string
        Name of output file

    Returns
    -------
    list_outfnames : list of strings of output file names

    """

    if (file_list != None) and (data_dir != None):
        raise RuntimeWarning(
            "file_list and data_dir both set, only the data_dir will be used."
        )

    # Check the aggregation methods are okay
    agg_types = ["mean", "median", "sum", "perc95", "perc5"]
    aggcheck = [a for a in agg if a in agg_types]
    if aggcheck is None:
        raise ValueError("Invalid Aggregation type. Expected any of: %s" % agg_types)
    else:
        print("Finding", aggcheck, " out of possible", agg_types)

    # If a directory has been passed, add all the files to the list
    if data_dir is not None:
        # data_dir = '/path/to/data'
        print("Reading all *.tif files in: ", data_dir)
        file_list = glob(os.path.join(data_dir, "*.tif"))

    # Get metadata from one of the input files
    with rasterio.open(file_list[0]) as src:
        meta = src.meta

    meta.update(dtype=rasterio.float32)

    # Stack all data/channels as a list of numpy arrays
    array_list = []
    for x in file_list:
        array_list.append(_read_file(x))

    array_list = np.asarray(array_list)

    # Perform aggregation over channels axis
    mean_array = np.nanmean(array_list, axis=0)
    median_array = np.nanmedian(array_list, axis=0)
    sum_array = np.nansum(array_list, axis=0)
    mean_array95 = np.nanpercentile(array_list, 95, axis=0)
    mean_array5 = np.nanpercentile(array_list, 5, axis=0)

    aggdict = {}
    aggdict["mean"] = mean_array
    aggdict["median"] = median_array
    aggdict["sum"] = sum_array
    aggdict["perc95"] = mean_array95
    aggdict["perc5"] = mean_array5

    # Write output file
    list_outfnames = []
    for a in aggcheck:
        with rasterio.open(outfile + "_" + a + ".tif", "w", **meta) as dst:
            dst.write(aggdict[a].astype(rasterio.float32), 1)
        print(a, "of filelist saved in: ", outfile + "_" + a + ".tif")
        list_outfnames.append(outfile + "_" + a + ".tif")
    return list_outfnames


def aggregate_multiband(
    file_list=None, data_dir=None, agg=["mean"], outfile="aggregation"
):
    """
    Aggregates over multiple files but keeps channels independently.
    Results are written to new tif files.

    Parameters
    ----------
    file_list : list of strings
        List of files to aggregate
    data_dir : string
        Path to directory containing files
    agg : list of strings
        List of aggregation methods to apply
    outfile : string
        Name of output file

    Returns
    -------
    outfname_list : list of strings of output file names
    channel_list : list of strings of channel names
    agg_list : list of strings of aggregation methods
    """

    if (file_list != None) and (data_dir != None):
        raise RuntimeWarning(
            "file_list and data_dir both set, only the data_dir will be used."
        )

    # Check the aggregation methods are okay
    agg_types = ["mean", "median", "sum", "perc95", "perc5"]
    aggcheck = [a for a in agg if a in agg_types]
    if aggcheck is None:
        raise ValueError("Invalid Aggregation type. Expected any of: %s" % agg_types)
    else:
        print("Finding", aggcheck, " out of possible", agg_types)

    # If a directory has been passed, add all the files to the list
    if data_dir is not None:
        # data_dir = '/path/to/data'
        print("Reading all *.tif files in: ", data_dir)
        file_list = glob(os.path.join(data_dir, "*.tif"))

    # Get metadata from one of the input files
    with rasterio.open(file_list[0]) as src:
        meta = src.meta
        desc = src.descriptions

    meta.update(dtype=rasterio.float32)

    # Append all tif files for each channel as a list of numpy arrays
    array_list = {k: [] for k in desc}

    for x in file_list:
        # print(x)
        data = _read_file(x)
        if data.shape[0] != len(desc):
            print("Band number mismatch between files!")
        for i in range(data.shape[0]):
            # print(i,desc[i])
            array_list[desc[i]].append(data[i, :, :])

    # Perform aggregation over channels axis
    outfname_list = []
    channel_list = []
    agg_list = []
    for i, channel in enumerate(array_list):
        mean_array = np.nanmean(array_list[channel], axis=0)
        median_array = np.nanmedian(array_list[channel], axis=0)
        sum_array = np.nansum(array_list[channel], axis=0)
        mean_array95 = np.nanpercentile(array_list[channel], 95, axis=0)
        mean_array5 = np.nanpercentile(array_list[channel], 5, axis=0)

        aggdict = {}
        aggdict["mean"] = mean_array
        aggdict["median"] = median_array
        aggdict["sum"] = sum_array
        aggdict["perc95"] = mean_array95
        aggdict["perc5"] = mean_array5

        # Write output file
        for a in aggcheck:
            outstring = outfile + "_" + a + "_channel_" + channel + ".tif"
            with rasterio.open(
                outstring, "w", **meta
            ) as dst:
                dst.write(aggdict[a].astype(rasterio.float32), 1)
            print(
                a,
                "of filelist saved in: ",
                outstring,
            )
            outfname_list.append(outstring)
            agg_list.append(a)
            channel_list.append(str(i))
    return outfname_list, channel_list, agg_list



def extract_values_from_rasters(coords, raster_files, method = "nearest"):
    """
    Extract values from a list of raster files at given coordinates using rioxarray.
    Values will be extracted for all bands in each raster file.
    Return geopandas DataFrame with extracted values and geometry.

    Input:
        coords: A list of tuples containing longitude and latitude coordinates.
                Format: [(lng1, lat1), (lng2, lat2), ...]

        raster_files: A list of raster file paths.
                      Format: ["path/to/raster1.tif", "path/to/raster2.tif", ...]

        method: The method to select values from raster files for 
                inexact matches between input coords and raster coords:
                 {"nearest", "pad", "ffill", "backfill", "bfill"}, optional
            - nearest (Default): use nearest valid index value. 
            - pad / ffill: propagate last valid index value forward
            - backfill / bfill: propagate next valid index value backward
            - None: only exact matches

    Output:
        A geopandas DataFrame containing the extracted values and geometry, where each row represents
        a coordinate point and the columns represent the bands for each raster file.
        Output column names are the raster file name plus the band name.
    """
    all_coords_data = []
    column_names = []

    with spin("Extracting values from raster files...", "blue") as s:
        for raster_file in raster_files:
            # Open the raster file with rioxarray
            ds = rxr.open_rasterio(raster_file)
            
            # Extract values for all coordinates
            coords_data = []
            for lng, lat in coords:
                # Select the nearest lat and lon coordinates from the dataset
                data = ds.sel(x=lng, y=lat, method=method)
                
                # Convert the data to a numpy array and flatten it
                data_array = data.values.flatten().tolist()
                
                # Add the extracted values to the list
                coords_data.append(data_array)

            # Concatenate the extracted values from all raster files
            all_coords_data.append(coords_data)

            # try to det the band names from the dataset, otherwise use the band number
            try:
                band_names = ds.attrs['long_name']
                if isinstance(band_names, str):
                    band_names = [band_names]
                if isinstance(band_names, tuple):
                    band_names = list(band_names)
                if len(band_names) != len(ds.band.values.tolist()):
                    band_names = ds.band.values.tolist()
            except:
                band_names = ds.band.values.tolist()
            # get the raster name
            raster_name = os.path.basename(raster_file).split(".")[0]
            # Add the raster name to the band names
            band_names = [f"{raster_name}_{band_name}" for band_name in band_names]

            # Add the band names to the column names list
            column_names.extend(band_names)

    # Convert the data to a pandas DataFrame and include the column names
    all_coords_data = pd.DataFrame(np.hstack(all_coords_data), columns=column_names)
    
    # Check for potential duplicate column names in all_coords_data
    if all_coords_data.columns.duplicated().any():
        print("Duplicate column names found. Please check the input raster files.")
        # drop duplicate columns and leave only first occurence
        all_coords_data = all_coords_data.loc[:,~all_coords_data.columns.duplicated()].copy()

    # save all_coords_data with coords as geopackage with geopandas
    gdf = gpd.GeoDataFrame(all_coords_data, geometry=gpd.points_from_xy(coords[:,0], coords[:,1]), crs="EPSG:4326")

    # insert the coords into the dataframe
    gdf.insert(0, 'Longitude', coords[:,0])
    gdf.insert(1, 'Latitude', coords[:,1])

    return gdf


def colour_geotiff_and_save_cog(input_geotiff, colour_map):
    """
    Colorizes a GeoTIFF image using a specified color map and saves it as a COG (Cloud-Optimized GeoTIFF).

    Args:
        input_geotiff (str): The path to the input GeoTIFF file.
        colour_map (str): The name of the color map to use for colorizing the image.

    Raises:
        Exception: If unable to convert the colored GeoTIFF to a COG.

    Returns:
        None
    """
    
    output_colored_tiff_filename = input_geotiff.replace('.tif', '_colored.tif')
    output_cog_filename = input_geotiff.replace('.tif', '_cog.tif')
    
    with rasterio.open(input_geotiff) as src:
        meta = src.meta.copy()
        dst_crs = rasterio.crs.CRS.from_epsg(4326) #change so not hardcoded?
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

        meta.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        tif_data = src.read(1, masked=True).astype('float32') #setting masked=True here tells rasterio to use masking information if present, but we need to add the mask itself first.
        tif_formatted = tif_data.filled(np.nan)

        cmap = cm.get_cmap(colour_map) #can also use 'terrain' cmap to keep this the same as the preview image from above.
        na = tif_formatted[~np.isnan(tif_formatted)]

        min_value = min(na)
        max_value = max(na)

        norm = Normalize(vmin=min_value, vmax=max_value)

        coloured_data = (cmap(norm(tif_formatted))[:, :, :3] * 255).astype(np.uint8)

        meta.update({"count":3})


        with rasterio.open(output_colored_tiff_filename, 'w', **meta) as dst:
            reshape = reshape_as_raster(coloured_data)
            dst.write(reshape)

    try:
        dst_profile = cog_profiles.get('deflate')
        with MemoryFile() as mem_dst:
            cog_translate(
                output_colored_tiff_filename,
                output_cog_filename,
                config=dst_profile,
                in_memory=True,
                dtype="uint8",
                add_mask=False,
                nodata=0,
                dst_kwargs=dst_profile
            )
        
    except:
        raise Exception('Unable to convert to cog')