#!/bin/python
"""
Utility functions for for spatial processing.

raster_buffer: Given a longitude,latitude point, a raster file, and a buffer
    region, find the values of all points in circular buffer.
_get_features(internal): Parse features from GeoDataFrame format to Rasterio
    format
_coreg_polygon(internal): Crops a raster to a polygon shape.
raster_polygon_buffer: Given list of longitudes and latitudes defining a
    polygon, crop raster file, return the values of all points in the polygon.
"""

from glob import glob
import os
import json

import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling

import numpy as np
import pandas as pd
import geopandas as gpd

from pyproj import CRS
from geodata_fetch import utils

from shapely.geometry import Polygon
from fiona.crs import from_epsg
from shapely.geometry import Polygon



def raster_buffer(long, lat, raster, buffer):
    """
    given a longitude,latitude point, a raster file, and a buffer region,
        return the values of all points in circular buffer.

    INPUTS:
    long: longitude point of interest
    lat: latitude point of interest
    raster: file path/name (as string)
    buffer: integer, raster array pixel units to return values for

    RETURNS
    values: list of raster array values around point of interest.
    """
    print("Opening:", raster)
    raster = rasterio.open(raster)

    # Get the transformation crs data
    gt  = raster.transform

    # Interogate the tiff file as an array
    # This will only be the first band, usally multiband has same index.
    arr = raster.read(1)

    # FIXME Check the number of bands and print a warning if more than 1

    # Shape of raster
    print("Raster pixel size:", np.shape(arr))

    # get row/column index of point
    point = utils._get_coords_at_point(gt, long, lat)

    # get values of data array at the buffer-index locations
    values = _coreg_buffer(point[0], point[1], arr, buffer)

    return(values)


def _get_features(gdf):
    """
    Function to parse features from GeoDataFrame in such a manner that
        rasterio wants them

    gdf: geodataframe of a geometry polygon.
    """
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


def _coreg_polygon(data, polygon):
    """
    Crops a raster to a polygon shape.

    INPUTS
    data: gdal raster object.
    polygon: Shapely Polygon defining area to crop.

    RETURNS
    out_img: Returns array of values inside the polygon.
    TODO: instead of hardcoding the epsg, it should be pulled from the input raster.
    """
    geo = gpd.GeoDataFrame({'geometry': polygon}, index=[0], crs=from_epsg(4326))
    geo = geo.to_crs(crs=data.crs.data)
    coords = _get_features(geo)
    out_img, _ = mask(data, shapes=coords, crop=True)

    return(out_img)


def raster_polygon_buffer(lngs, lats, raster):
    """
    Given a list of longitudes and latitudes that define a polygon, crop a
        raster file, and return the values of all points in the polygon.

    INPUTS:
    lngs: list of longitudes
    lats: list of latitudes
    raster: file path/name (as string) of raster

    RETURNS
    values: list of raster array values inside polygon.
    """
    if (len(lngs) != len(lats)):
        raise ValueError("Longitude and Latitude list should be equal in length\
            representing pairs of points defining a polygon.")

    print("Opening:", raster)
    raster = rasterio.open(raster)

    # get row/column index of point
    polygon = Polygon(list(zip(lngs, lats)))

    # get values of data array at the buffer-index locations
    values = _coreg_polygon(raster, polygon)

    return(values)