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

from glob import glob
import os
import json

from types import SimpleNamespace

import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.plot import show
from rasterio.dtypes import uint8

import rioxarray as rxr
from shapely.geometry import box #try and remove later

from owslib.wcs import WebCoverageService

import numpy as np
import pandas as pd
import geopandas as gpd


from pyproj import CRS
from pathlib import Path

from numba import jit

import warnings
import logging


from alive_progress import alive_bar, config_handler


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

def load_settings(fname_settings):
    # Load settings from yaml file
    with open(fname_settings, "r") as f:
        settings = json.load(f)
        
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


def reproj_mask(filename, input_filepath, bbox, crscode, output_filepath):
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
    masked_filepath = "masked_" + filename
    mask_outpath = os.path.join(output_filepath, masked_filepath)
    
    input_raster = rxr.open_rasterio(input_full_filepath)
    clipped = input_raster.rio.clip(bbox.geometry.values)
    clipped.rio.to_raster(mask_outpath, tiled=True)

    return clipped

def reproj_rastermatch(infile, matchfile, outfile, nodata):
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
    # open input
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
        print(
            "Coregistered to shape:", dst_height, dst_width, "\n Affine", dst_transform
        )
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


def reproj_raster(
    infile, outfile, bbox_out, resolution_out=None, crs_out="EPSG:4326", nodata=0
):
    """
    Reproject and clip for a given output resolution, crs and bbox.
    Output file is written to disk.

    Parameters
    ----------
    infile : (string) path to input file to reproject
    outfile : (string) path to output file tif
    bbox_out : (left, bottom, right, top)
    resolution_out : (float) resolution of output raster
    crs_out : default "EPSG:4326"
    nodata : (float) nodata value for output raster
    """
    # open input
    with rasterio.open(infile) as src:
        src_transform = src.transform

        width_out = int((bbox_out[2] - bbox_out[0]) / resolution_out)
        height_out = int((bbox_out[3] - bbox_out[1]) / resolution_out)

        # calculate the output transform matrix
        dst_transform, dst_width, dst_height = calculate_default_transform(
            src.crs,  # input CRS
            crs_out,  # output CRS
            width_out,  # output width
            height_out,  # output height
            *bbox_out,  # unpacks input outer boundaries (left, bottom, right, top)
        )

        # set properties for output
        dst_kwargs = src.meta.copy()
        dst_kwargs.update(
            {
                "crs": crs_out,
                "transform": dst_transform,
                "width": dst_width,
                "height": dst_height,
                "nodata": nodata,
            }
        )
        print("Converting to shape:", dst_height, dst_width, "\n Affine", dst_transform)
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
                    dst_crs=crs_out,
                    resampling=Resampling.nearest,
                )


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


@jit(nopython=True)
def _get_coords_at_point(gt, lon, lat):
    """
    Internal function, given a point in some coordinate reference
    (e.g. lat/lon) Find the closest point to that in an array (e.g.
    a raster) and return the index location of that point in the raster.
    
    INPUTS:
        gt: output from "gdal_data.GetGeoTransform()"
        lon: x/row-coordinate of interest
        lat: y/column-coordinate of interest
    
    RETURNS:
        col: x index value from the raster
        row: y index value from the raster
    """
    row = int((lon - gt[2]) / gt[0])
    col = int((lat - gt[5]) / gt[4])

    return (col, row)


def raster_query(longs, lats, rasters, titles=None):
    """
    DEPRECATED: Use extract_values_from_rasters instead.

    given a longitude,latitude value, return the value at that point of the
        first channel/band in the raster/tif.

    INPUTS
        longs:list of longitudes
        lats:list of latitudes
        rasters:list of raster filenames (as strings)
        titles:list of column titles (as strings) that correspond to rasters (if none provided, rasternames will be used)

    RETURNS
        gdf: geopandas dataframe where each row is long/lat point,
            and columns are rasterfiles
    """

    # Setup the dataframe to store the ML data
    gdf = gpd.GeoDataFrame(
        {"Longitude": longs, "Latitude": lats},
        geometry=gpd.points_from_xy(longs, lats),
        crs="EPSG:4326",
    )

    # Loop through each raster
    for filepath in rasters:
        filename = Path(filepath).resolve().stem
        # print("Opening:", filename)
        # Open the file:
        raster = rasterio.open(filepath)
        # Get the transformation crs data
        gt = raster.transform

        # This will only be the first band, usally multiband has same index.
        arr = raster.read(1)

        if titles is not None:
            colname = titles[rasters.index(filepath)]
        else:
            colname = Path(filepath).stem
            # colname = filepath.split("/")[-1][:-4]

        # Interogate the tiff file as an array

        # FIXME Check the number of bands and print a warning if more than 1

        # Shape of raster
        # print("Raster pixel size:", np.shape(arr))

        # Slowest part of this function.
        # Speed up with Numba/Dask etc
        # (although previous attempts have not been worth it.)
        # Query the raster at the points of interest
        with spin(f"• {filename} | pixel size: {np.shape(arr)}", "blue") as s:
            values = []
            for (lon, lat) in zip(longs, lats):

                # Convert lat/lon to raster units-index
                point = _get_coords_at_point(gt, lon, lat)

                # This will fail for small areas or on boundaries
                try:
                    val = arr[point[0], point[1]]
                except:
                    # print(lon,lat,point[0],point[1],"has failed.")
                    val = 0
                values.append(val)
            s(1)

        # dd the values at the points to the dataframe
        gdf[filepath] = values
        gdf = gdf.rename(columns={filepath: colname})

    return gdf


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


@jit(nopython=True)
def points_in_circle(circle, arr):
    """
    A generator to return all points whose indices are within a given circle.
    http://stackoverflow.com/a/2774284
    Warning: If a point is near the the edges of the raster it will not loop
    around to the other side of the raster!

    INPUTS
    circle: a tuple of (i0, j0, r) where i0, j0 are the indices of the center of the circle and r is the radius

    arr: a two-dimensional numpy array

    RETURNS
    A generator that yields all points within the circle    
    """
    i0, j0, r = circle

    def intceil(x):
        return int(np.ceil(x))

    for i in range(intceil(i0 - r), intceil(i0 + r)):
        ri = np.sqrt(r**2 - (i - i0) ** 2)
        for j in range(intceil(j0 - ri), intceil(j0 + ri)):
            if (i >= 0 and i < len(arr[:, 0])) and (j >= 0 and j < len(arr[0, :])):
                yield arr[i][j]


def coreg_raster(i0, j0, data, region):
    """
    Coregisters a point with a buffer region of a raster.
    
    INPUTS
        i0: column-index of point of interest
        j0: row-index of point of interest
        data: two-dimensional numpy array (raster)
        region: integer, same units as data resolution

    RETURNS
        pts: all values from array within region
    """
    pts_iterator = points_in_circle((i0, j0, region), data)
    pts = np.array(list(pts_iterator))

    return pts