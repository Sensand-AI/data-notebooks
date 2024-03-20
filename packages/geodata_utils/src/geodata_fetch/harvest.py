import os
from pathlib import Path
import geopandas as gpd
import numpy as np
from datetime import datetime, timedelta

from geodata_fetch import getdata_slga,getdata_dem, getdata_radiometric, utils
from geodata_fetch.utils import  load_settings, reproj_mask, list_tif_files


def run(path_to_config, input_geom):
    print("Starting the data harvester -----")

    settings = load_settings(path_to_config)
    property_name = settings.property_name
    output_data_dir = os.path.join(settings.outpath, "data")
    output_masked_data_dir = os.path.join(settings.outpath, "masked-data")
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
        raise ValueError("No bounding box provided")

    # Temporal range
    # convert date strings to datetime objects
    date_diff = (datetime.strptime(settings.date_end, "%Y-%m-%d") 
        - datetime.strptime(settings.date_start, "%Y-%m-%d")).days
    if settings.time_intervals > 0:
        period_days = date_diff / settings.time_intervals
        if period_days == 0:
            period_days = 1
    else:
        period_days = None

    # process each data source
    utils.msg_info(
        f"Found the following {count_sources} sources: {list_sources}")
    print("\nDownloading from API sources -----")

#-----add getdata functions here---------------------------------------------------------#

    if "SLGA" in list_sources:
        print("Downloading SLGA data...")
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
        except Exception as e:
            print(e)
        var_exists = "files_slga" in locals() or "files_slga" in globals()
        if var_exists:
            if len(files_slga) != len(slga_layernames):
                # get filename stems of files_slga
                slga_layernames = [Path(f).stem for f in files_slga] # check this still works afer adding sub-dirs
        else:
            pass
    
    
    if "DEM" in list_sources:
        print("Downloading DEM data...")
        dem_layernames = settings.target_sources["DEM"]
        try:
            files_dem = getdata_dem.get_dem_layers(
                property_name=property_name,
                layernames=dem_layernames,
                bbox=settings.target_bbox,
                outpath=output_data_dir
            )
        except Exception as e:
            print(e)
            # Check if output if False (no data available) and skip if so
        var_exists = "files_dem" in locals() or "files_dem" in globals()
        if var_exists:
            if len(files_dem) != len(dem_layernames):
                # get filename stems of files_slga
                dem_layernames = [Path(f).stem for f in files_dem]
        else:
            pass
        
        
    if "Radiometric" in list_sources:
        print("Downloading Radiometric data...")
        rm_layernames = settings.target_sources["Radiometric"]
        try:
            files_rm = getdata_radiometric.get_radiometric_layers(
                property_name=property_name,
                layernames=rm_layernames,
                bbox=settings.target_bbox,
                outpath=output_data_dir
            )
        except Exception as e:
            print(e)
        var_exists = "files_rm" in locals() or "files_rm" in globals()
        if var_exists:
            rm_layernames = [Path(f).stem for f in files_rm]
        else:
            pass

#--------------------------------------------------------------------------------------#
    """
    Add function here to apply mask and save copy of geotifs as COGS if mask boolean set to True.
    Use rioxarray to force tiled tifs aka COGs.
    """
    
    if data_mask is True:
        print("data mask is True")
        os.makedirs(output_masked_data_dir, exist_ok=True)
        
        # make a list of all the tif files in the 'data' package that were harvested from sources
        tif_files = list_tif_files(output_data_dir)
        try:
            for tif in tif_files:
                # Clips a raster to the area of a shape, and reprojects.
                masked_data = reproj_mask(
                    filename=tif,
                    input_filepath = output_data_dir,
                    bbox=input_geom,
                    crscode=4326,
                    output_filepath=output_masked_data_dir)
        except Exception as e:
            print(e)
    else:
        print("data mask is false")

    print("\nHarvest complete")
