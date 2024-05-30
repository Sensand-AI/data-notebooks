import os
import sys
import logging
from pathlib import Path
import geopandas as gpd
import numpy as np
from datetime import datetime, timedelta

from geodata_fetch import getdata_slga,getdata_dem, getdata_radiometric
from geodata_fetch.utils import  load_settings, reproj_mask

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

def run(path_to_config, input_geom):
    logger.info("Starting the data harvester")

    settings = load_settings(path_to_config)
    target_crs = settings.target_crs
    add_buffer = settings.add_buffer
    resample = settings.resample
    property_name = settings.property_name
    output_data_dir = settings.outpath #removing sub-dirs as they mess up lambda.
    #output_data_dir = os.path.join(settings.outpath, "data")
    #output_masked_data_dir = os.path.join(settings.outpath, "masked-data")
    data_mask = settings.data_mask
    
    # Count number of sources to download from
    count_sources = len(settings.target_sources)
    list_sources = list(settings.target_sources.keys())

    # Set coordinates absed on the lat and long given in input file
    longs = settings.target_centroid_lng
    lats = settings.target_centroid_lat
    coords = np.vstack((longs, lats)).T


    # Stop if bounding box cannot be calculated or was not provided
    if settings.target_bbox is None:
        logger.error("No bounding box provided")
    
    if settings.add_buffer is True:
        # Add buffer to the bounding box
        input_geom = input_geom.buffer(0.002, join_style=2, resolution=15)
        logger.info("Adding buffer to AOI")

    # Temporal range
    # convert date strings to datetime objects
    
    # date_diff = (datetime.strptime(settings.date_end, "%Y-%m-%d") 
    #     - datetime.strptime(settings.date_start, "%Y-%m-%d")).days
    # if settings.time_intervals > 0:
    #     period_days = date_diff / settings.time_intervals
    #     if period_days == 0:
    #         period_days = 1
    # else:
    #     period_days = None

    # process each data source
    logger.info(f"Requested the following {count_sources} sources: {list_sources}")

#-----add getdata functions here---------------------------------------------------------#

    if "SLGA" in list_sources:
        logger.info("Begin fetching SLGA data.")
        slga_layernames = list(settings.target_sources["SLGA"].keys())
        # get min and max depth for each layername
        depth_min = []
        depth_max = []
        for layername in slga_layernames:
            depth_bounds = settings.target_sources["SLGA"][layername]
            dmin, dmax = getdata_slga.identifier2depthbounds(depth_bounds)
            depth_min.append(dmin)
            depth_max.append(dmax)
        try:
            files_slga = getdata_slga.get_slga_layers(
                property_name=property_name,
                layernames=slga_layernames,
                bbox=settings.target_bbox,
                outpath=output_data_dir,
                depth_min=depth_min,
                depth_max=depth_max,
                get_ci=False, #can this be added to the settings.json instead of being hard-coded here?
            )
            logger.info(f"SLGA data downloaded successfully: {files_slga}")
        except Exception as e:
            logger.error(f"Error fetching SLGA data: {e}")
            
        #var_exists = "files_slga" in locals() or "files_slga" in globals()
        # if var_exists:
        #     if len(files_slga) != len(slga_layernames):
        #         # get filename stems of files_slga
        #         slga_layernames = [Path(f).stem for f in files_slga] # check this still works afer adding sub-dirs
        # else:
        #     pass
    
    
    if "DEM" in list_sources:
        logger.info("Begin fetching DEM data.")
        dem_layernames = settings.target_sources["DEM"]
        try:
            files_dem = getdata_dem.get_dem_layers(
                property_name=property_name,
                layernames=dem_layernames,
                bbox=settings.target_bbox,
                outpath=output_data_dir
            )
        except Exception as e:
            logger.error(f"Error fetching DEM data: {e}")
            # Check if output if False (no data available) and skip if so
        # var_exists = "files_dem" in locals() or "files_dem" in globals()
        # if var_exists:
        #     if len(files_dem) != len(dem_layernames):
        #         # get filename stems of files_slga
        #         dem_layernames = [Path(f).stem for f in files_dem]
        # else:
        #     pass
        
        
    if "Radiometric" in list_sources:
        logger.info("Begin fetching RadMap data.")
        rm_layernames = settings.target_sources["Radiometric"]
        try:
            files_rm = getdata_radiometric.get_radiometric_layers(
                property_name=property_name,
                layernames=rm_layernames,
                bbox=settings.target_bbox,
                outpath=output_data_dir
            )
        except Exception as e:
            logger.error(f"Error fetching RadMap data: {e}")
        # var_exists = "files_rm" in locals() or "files_rm" in globals()
        # if var_exists:
        #     rm_layernames = [Path(f).stem for f in files_rm]
        # else:
        #     pass

#-----apply masking to files if flag true---------------------------------------------------------#
    
    if data_mask is True:
        logger.info("Mask is true, applying to geotifs.")
        
        # make a list of all the tif files in the 'data' package that were harvested from sources
        tif_files = [f for f in os.listdir(output_data_dir) if f.endswith('.tiff') and not f.endswith(("_masked.tiff", "_colored.tiff", "_cog.tiff", "_cog.public.tiff"))]
    
        logger.info(f"files to mask: {tif_files}")
        for tif in tif_files:
            # Clips a raster to the area of a shape, and reprojects.
            masked_data = reproj_mask(
                filename=tif,
                input_filepath=output_data_dir,
                bbox=input_geom,
                crscode=target_crs,
                output_filepath=output_data_dir,
                resample=resample)
            return masked_data #may need to edit, as it returns first one and breaks loop.
