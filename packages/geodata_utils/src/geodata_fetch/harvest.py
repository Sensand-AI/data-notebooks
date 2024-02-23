"""
This script is running the headless version of the geodata-harvester.

The following main steps are automatically executed within the run() function:
    - loading settings from config file
    - creating bounding box from input file points if not provided
    - downloading data layers as specified in config file
    - processing data layers as specified in config file
    - save downloaded image files to disk as GeoTiffs
    - save summary table of downloaded files as CSV
    - extract data for point locations provided in input file (name specified in settings)
    - save extracted point results to disk as CSV and as geopackage 

Example call within Python:
    from geodata_harvester import harvest
    harvest.run(path_to_config))
"""


import os
from pathlib import Path
import geopandas as gpd
from termcolor import cprint
import yaml
import shutil
import argparse
import numpy as np
from datetime import datetime, timedelta

from geodata_lite import (getdata_slga, utils, temporal, spatial)
from geodata_lite.utils import init_logtable, update_logtable, load_settings


def run(path_to_config, log_name="download_summary", preview=False, return_df=False):
    """
    A headless version of the Data-Harvester (with some limitations).
    Results are saved to disk.

    Parameters
    ----------
    path_to_config : str
        Path to YAML config file
    log_name: name of log file (default: "download_log")
    preview : bool, optional
        Plots a matrix of downloaded images if set to True, by default False
    return_df : bool, optional (Default: False)
        if True, returns dataframe with results

    Returns
    -------
    None (if return_df is False)
    dataframe (if return_df is True)
    """
    cprint("Starting the data harvester -----", "magenta", attrs=["bold"])

    # Load config file (based on notebook for now, will optimise later)
    
    """
    NOTE: load_settings was in harvesterwidgets, but in the slimmed version could probably just go into utils. JAG.
    """
    settings = load_settings(path_to_config)

    # Count number of sources to download from
    count_sources = len(settings.target_sources)
    list_sources = list(settings.target_sources.keys())

    # If no infile provided, generate a blank one (including colnames)
    try:
        settings.infile
        if settings.infile is None:
            points_available = False
        else:
            points_available = True
    except (AttributeError, KeyError):
        settings.infile = None
        settings.colname_lng = None
        settings.colname_lat = None
        points_available = False

    # If no resolution set, make it 1 arc-second
    if settings.target_res is None:
        utils.msg_info(
            "No target resolution specified, using default of 1 arc-sec")
        settings.target_res = 1

    # Create bounding box if infile is provided and target_bbox is not provided
    if settings.infile is not None:
        gdfpoints = gpd.read_file(settings.infile)
        longs = gdfpoints[settings.colname_lng].astype(float)
        lats = gdfpoints[settings.colname_lat].astype(float)
        coords = np.vstack((longs, lats)).T

        if settings.target_bbox is None:
            settings.target_bbox = (
                min(longs) - 0.05,
                min(lats) - 0.05,
                max(longs) + 0.05,
                max(lats) + 0.05,
            )

    # Stop if bounding box cannot be calculated or was not provided
    if settings.infile is None and settings.target_bbox is None:
        raise ValueError("No sampling file or bounding box provided")

    # Temporal range
    # convert date strings to datetime objects
    date_diff = (datetime.strptime(settings.date_max, "%Y-%m-%d") 
        - datetime.strptime(settings.date_min, "%Y-%m-%d")).days
    if settings.time_intervals is not None:
        period_days = date_diff // settings.time_intervals
        if period_days == 0:
            period_days = 1
    else:
        period_days = None

    # Create download log
    download_log = init_logtable()
    # process each data source
    utils.msg_info(
        f"Found the following {count_sources} sources: {list_sources}")
    cprint("\nDownloading from API sources -----", "magenta", attrs=["bold"])


    if "SLGA" in list_sources:
        cprint("\n⌛ Downloading SLGA data...", attrs=["bold"])
        # get data from SLGA
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
                slga_layernames,
                settings.target_bbox,
                settings.outpath,
                depth_min=depth_min,
                depth_max=depth_max,
                get_ci=True,
            )
        except Exception as e:
            print(e)
        var_exists = "files_slga" in locals() or "files_slga" in globals()
        if var_exists:
            if len(files_slga) != len(slga_layernames):
                # get filename stems of files_slga
                slga_layernames = [Path(f).stem for f in files_slga]
            download_log = update_logtable(
                download_log,
                files_slga,
                slga_layernames,
                "SLGA",
                settings,
                layertitles=[],
                loginfos="downloaded",
            )
        else:
            pass

    # save log to file
    download_log.to_csv(os.path.join(settings.outpath, log_name + ".csv"), index=False)

    # extract filename from settings.infile
    # Select all processed data
    df_sel = download_log.copy()
    rasters = df_sel["filename_out"].values.tolist()
    titles = df_sel["layertitle"].values.tolist()
    if points_available:
        fn = Path(settings.infile).resolve().name
        cprint(
            f"\nExtracting data points for {fn}  -----", "magenta", attrs=["bold"])
        # Extract datatable from rasters given input coordinates
        # gdf = utils.raster_query(longs, lats, rasters, titles) # old slower version
        gdf = utils.extract_values_from_rasters(coords, rasters)
        # Save as geopackage
        gdf.to_file(os.path.join(settings.outpath,
                    "results.gpkg"), driver="GPKG")
        # Save the results table to a csv as well
        gdf.drop("geometry", axis=1).to_csv(
            os.path.join(settings.outpath, "results.csv"), index=True, mode="w"
        )
        utils.msg_success(
            f"Data points extracted to {settings.outpath}results.gpkg")

    if preview and points_available:
        utils.plot_rasters(rasters, longs, lats, titles)
    elif preview and not points_available:
        utils.plot_rasters(rasters, titles=titles)

    cprint("\n🎉 🎉 🎉 Harvest complete 🎉 🎉 🎉", "magenta", attrs=["bold"])

    if return_df and points_available:
        return gdf
    else:
        return None