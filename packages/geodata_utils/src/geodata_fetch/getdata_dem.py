
import logging
import os
from datetime import datetime, timezone
from geodata_fetch import utils
from geodata_fetch.utils import spin, get_wcs_capabilities
from geodata_fetch import arc2meter

import rasterio

# logger setup
from geodata_fetch import write_logs
from owslib.wcs import WebCoverageService
from rasterio.plot import show
import rioxarray
import numpy as np

import json
import importlib.resources #to read in slga.json during runtime



def get_demdict():
    with importlib.resources.open_text('config','ga_dem_urls.json') as f:
        dem_json = json.load(f)

    
    demdict = {}
    demdict["title"] = dem_json["title"]
    demdict["description"] = dem_json["description"]
    demdict["license"] = dem_json["license"]
    demdict["source_url"] = dem_json["source_url"]
    demdict["copyright"] = dem_json["copyright"]
    demdict["attribution"] = dem_json["attribution"]
    demdict["crs"] = dem_json["crs"]
    demdict["bbox"] = dem_json["bbox"]
    demdict["resolution_arcsec"] = dem_json["resolution_arcsec"]
    demdict["layer_names"] = dem_json["layer_names"]
    demdict["layers_url"] = dem_json["layers_url"]


    return demdict

"""
have copied to utils, try using that version of get_capabilities().
"""

# def get_wcs_capabilities(url):
#     """
#     Get capabilities from WCS layer.

#     Parameters
#     ----------
#     url : str
#         layer url

#     Returns
#     -------
#     keys    : list
#         layer identifiers
#     titles  : list  of str
#         layer titles
#     descriptions : list of str
#         layer descriptions
#     bboxs   : list of floats
#         layer bounding boxes
#     """

#     # Create WCS object
#     wcs = WebCoverageService(url, version="1.0.0", timeout=300)

#     # Get coverages and content dict keys
#     content = wcs.contents
#     keys = content.keys()

#     print("Following data layers are available:")
#     # Get bounding boxes and crs for each coverage
#     title_list = []
#     description_list = []
#     bbox_list = []
#     for key in keys:
#         print(f"key: {key}")
#         print(f"title: {wcs[key].title}")
#         title_list.append(wcs[key].title)
#         print(f"{wcs[key].abstract}")
#         description_list.append(wcs[key].abstract)
#         print(f"bounding box: {wcs[key].boundingBoxes}")
#         bbox_list.append(wcs[key].boundingBoxes)
#         print("")

#     return keys, title_list, description_list, bbox_list


"""
url="https://services.ga.gov.au/site_9/services/DEM_SRTM_1Second_Hydro_Enforced/MapServer/WCSServer?request=GetCapabilities&service=WCS"
crs="EPSG:4326"
resolution=1
verbose=False

"""
def getwcs_dem(url, crs, resolution, bbox, outpath):
    """
    Function to download and save geotiff from WCS layer.
    Parameters
    ----------
    outpath : str
        output directory for the downloaded file
        NOTE: The outpath is used here instead of an outfname because there's only 1 layer and we're naming the tif on its title. For the SLGA and others, there are multiple layers so this is set earlier based on the contents of the config and settings jsons.
    bbox : list
        layer bounding box
    resolution : int
        layer resolution in arcsec
    url : str
        url of wcs server
    crs: str

    Return
    ------
    Output filename
    """

    if resolution is None:
        resolution = get_demdict()["resolution_arcsec"]

    os.makedirs(outpath, exist_ok=True)
    # Create WCS object and get data
    try:
        with spin("Retrieving coverage from WCS server") as s:
            wcs = WebCoverageService(url, version="1.0.0", timeout=300)
            s(1)
        layername = wcs["1"].title
        fname_out = layername.replace(" ", "_") + ".tif"
        outfname = os.path.join(outpath, fname_out)
        if os.path.exists(outfname):
            utils.msg_warn(f"{fname_out} already exists, skipping download")
        else:
            with spin(f"Downloading {fname_out}") as s:
                data = wcs.getCoverage(
                    identifier="1",
                    bbox=bbox,
                    format="GeoTIFF",
                    crs=crs,
                    resx=resolution,
                    resy=resolution,
                )
                s(1)
            # Save data to file
            with open(outfname, "wb") as f:
                f.write(data.read())
    except Exception as e:
        print(e)
        utils.msg_err("Download failed, is the server down?")
        return False
    return outfname



def get_dem_layers(layernames, bbox, outpath):
    
    demdict = get_demdict()
    resolution = demdict["resolution_arcsec"]
    crs = demdict["crs"]
    layers_url = demdict["layers_url"]
    dem_url = layers_url["DEM"]
    
    fnames_out =  getwcs_dem(bbox, resolution, crs=crs, url=dem_url, resolution=resolution)
    return fnames_out