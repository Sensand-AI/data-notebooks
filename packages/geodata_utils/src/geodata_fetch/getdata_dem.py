
"""
Python script to download the Digital Elevation Model (DEM) of Australia derived from STRM with 1 Second Grid - Hydrologically Enforced

Core functionality:
- automatic download for the DEM-H via Web Coverage Service (WCS)
- clip data to custom bounding box
- save data as geotiff

The DEM layers, metadata, licensing and atttribution are described in the config folder in ga_dem_urls.json, and are read into a dictionary in the module function get_demdict()

"""
import os
import json
import logging
import importlib.resources #to read in slga.json during runtime
from geodata_fetch import utils
from geodata_fetch.utils import spin
from owslib.wcs import WebCoverageService



def get_demdict():
    with importlib.resources.open_text('config','dem.json') as f:
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
    demdict["layers_url"] = dem_json["layers_url"]

    return demdict

"""
have removed get_capabilities() from here and put in utils
"""

def getwcs_dem(url, crs, resolution, bbox, property_name, outpath):
    """
    Download and save geotiff from WCS layer
    
    Parameters
    ----------
    outpath : str
        output directory for the downloaded file
        NOTE: The outpath is used here instead of an outfname because there's only 1 layer and we're naming the tif on its title. For the SLGA and others, there are multiple layers so this is set earlier based on the contents of the config and settings jsons.
    bbox : list
        layer bounding box
    resolution : int
        layer resolution in arcsecond
    url : str
        url of wcs server
    crs: str
    outpath: str
        output directory for the downloaded file

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
        fname_out = layername.replace(" ", "_") + "_" + property_name + ".tif"
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



def get_dem_layers(property_name, layernames, bbox, outpath):
    """
    Download DEM-H layer and save as a geotif.

    Parameters
    ----------
    layernames : list of layer names (in this case, only 1)
    bbox : bounding box [min, miny, maxx, maxy] in
    outpath : output path

    Returns
    -------
    fnames_out : list of output file names
    """
    
    if not isinstance(layernames, list):
        layernames = [layernames]
        
    # Check if outpath exist, if not create it
    os.makedirs(outpath, exist_ok=True)

        
    demdict = get_demdict()
    resolution = demdict["resolution_arcsec"]
    # Convert resolution from arcsec to degree
    #resolution_deg = resolution / 3600.0
    
    # set target crs based on config json
    crs = demdict["crs"]
    layers_url = demdict["layers_url"]
    dem_url = layers_url["DEM"]
    
    fnames_out = []
    for layername in layernames:
        if layername == "DEM":
            outfname = getwcs_dem(url=dem_url, 
                                  crs=crs, 
                                  resolution=resolution, 
                                  bbox=bbox, 
                                  property_name=property_name, 
                                  outpath=outpath)
        fnames_out.append(outfname)
    
    return fnames_out