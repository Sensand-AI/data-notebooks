"""
This script contains the `DataHarvester` class and the `run` method.

The `DataHarvester` class is responsible for fetching geospatial data based on the provided configuration file and input geometry. It has the following attributes:
- `settings`: Stores the loaded settings from the configuration file.
- `input_geom`: Stores the input geometry that defines the area of interest.
- `target_sources`: Stores the target sources specified in the settings.
- `target_bbox`: Stores the target bounding box specified in the settings.
- `property_name`: Stores the property name specified in the settings.
- `output_data_dir`: Stores the output data directory specified in the settings.
- `target_crs`: Stores the target CRS specified in the settings.
- `resample`: Stores the resample method specified in the settings.
- `add_buffer`: Stores the add_buffer flag specified in the settings.
- `data_mask`: Stores the data mask flag specified in the settings.
- `fetched_files`: Stores the list of fetched files.

The `run` method is responsible for executing the data fetching process. It performs the following steps:
1. Adds a buffer to the input geometry if the add_buffer flag is True.
2. Sets the coordinates based on the latitude and longitude specified in the settings.
3. Counts the number of sources to download from and lists the source names.
4. Fetches data from the SLGA, DEM, and Radiometric sources based on the target sources specified in the settings.
5. Applies masking to the downloaded files if the data mask flag is True.

To use this script, create an instance of the `DataHarvester` class and call the `run` method with the path to the configuration file and the input geometry as parameters.
"""

import logging
import os
from pathlib import Path

import numpy as np
from shapely.geometry import Point

#from geodata_fetch import getdata_radiometric  # getdata_dem
from geodata_fetch.getdata_dem import dem_harvest  # updated call to dem using class
from geodata_fetch.getdata_slga import slga_harvest, identifier2depthbounds
from geodata_fetch.utils import load_settings, reproj_mask

logger = logging.getLogger()
# try this but remove if it doesn't work well with datadog:
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# class DataHarvesterOld:
#     def __init__(self, path_to_config, input_geom):
#         self.settings = load_settings(path_to_config)
#         self.input_geom = input_geom
#         self.target_sources = self.settings.target_sources
#         self.target_bbox = self.settings.target_bbox
#         self.property_name = self.settings.property_name
#         self.output_data_dir = self.settings.outpath
#         self.target_crs = self.settings.target_crs
#         self.resample = self.settings.resample
#         self.add_buffer = self.settings.add_buffer
#         self.data_mask = self.settings.data_mask
#         self.settings.lat = None
#         self.settings.long = None
#         self.fetched_files = []

#         self.dem_harvest = None
#         if "DEM" in self.settings.target_sources:
#             self.dem_harvest = dem_harvest()

#     def run(self):
#         if self.add_buffer is True:
#             # Add buffer to the bounding box
#             self.input_geom = self.input_geom.buffer(0.002, join_style=2, resolution=15)
#             print(f"Buffered geometry: {self.input_geom}")

#         if self.settings.lat is not None and self.settings.long is not None:
#             # Set coordinates based on the latitude and longitude
#             self.settings.lat = np.float64(self.settings.lat)
#             self.settings.long = np.float64(self.settings.long)
#             self.input_geom = Point(self.settings.long, self.settings.lat)

#         # Count number of sources to download from
#         self.count_sources = len(self.target_sources)
#         self.list_sources = list(self.target_sources.keys())

#         print(
#             f"Requested the following {self.count_sources} sources: {self.list_sources}"
#         )

#         # -----add getdata functions here---------------------------------------------------------#

#         if "SLGA" in self.target_sources:
#             slga_layernames = list(self.target_sources["SLGA"].keys())
#             # get min and max depth for each layername
#             depth_min = []
#             depth_max = []
#             for layername in slga_layernames:
#                 depth_bounds = self.target_sources["SLGA"][layername]
#                 dmin, dmax = self.getdata_slga.identifier2depthbounds(depth_bounds)
#                 depth_min.append(dmin)
#                 depth_max.append(dmax)
#             try:
#                 files_slga = self.slga_harvest.get_slga_layers(
#                     property_name=self.property_name,
#                     layernames=slga_layernames,
#                     bbox=self.target_bbox,
#                     outpath=self.output_data_dir,
#                     depth_min=depth_min,
#                     depth_max=depth_max,
#                     get_ci=False,  # can this be added to the settings.json instead of being hard-coded here?
#                 )

#                 slga_layernames = [Path(f).stem for f in files_slga]
#                 print(
#                     f"SLGA data downloaded successfully: {slga_layernames}"
#                 )  # consider replacing with individual success/fail message for each layer
#             except Exception as e:
#                 print(f"Error fetching SLGA data: {e}")

#         if "DEM" in self.target_sources:
#             dem_layernames = self.target_sources["DEM"]
#             try:
#                 self.dem_harvest.get_dem_layers(
#                     property_name=self.property_name,
#                     layernames=dem_layernames,
#                     bbox=self.target_bbox,
#                     outpath=self.output_data_dir,
#                 )
#             except Exception as e:
#                 print(f"Error fetching DEM data: {e}")

#         if "Radiometric" in self.target_sources:
#             rm_layernames = self.target_sources["Radiometric"]
#             try:
#                 files_rm = getdata_radiometric.get_radiometric_layers(
#                     property_name=self.property_name,
#                     layernames=rm_layernames,
#                     bbox=self.target_bbox,
#                     outpath=self.output_data_dir,
#                 )
#             except Exception as e:
#                 print(f"Error fetching RadMap data: {e}")

#         self._mask_data()

    # def _mask_data(self):
    #     if self.data_mask is True:
    #         print(f"Masking data in {self.output_data_dir}")

    #         # make a list of all the tif files in the 'data' package that were harvested from sources
    #         tif_files = [
    #             f
    #             for f in os.listdir(self.output_data_dir)
    #             if f.endswith(".tiff")
    #             and not f.endswith(
    #                 ("_masked.tiff", "_colored.tiff", "_cog.tiff", "_cog.public.tiff")
    #             )
    #         ]

    #         print(f"files to mask: {tif_files}")
    #         for tif in tif_files:
    #             # Clips a raster to the area of a shape, and reprojects.
    #             masked_data = reproj_mask(
    #                 filename=tif,
    #                 input_filepath=self.output_data_dir,
    #                 bbox=self.input_geom,
    #                 crscode=self.target_crs,
    #                 output_filepath=self.output_data_dir,
    #                 resample=self.resample,
    #             )
    #             return masked_data



#------------------refactoring attempt:-------------------------#
"""
JAG: attempting to refactor this module using concepts from the factory design pattern. 
Keep the fetching of each data source compartmentalised so core code logic doesn't need to be touched as new data sources are added.
"""

class Settings:
    def __init__(self, config):
        self.target_sources = config.target_sources
        self.target_bbox = config.target_bbox
        self.property_name = config.property_name
        self.outpath = config.outpath
        self.target_crs = config.target_crs
        self.resample = getattr(config, 'resample', False)
        self.add_buffer = getattr(config, 'add_buffer', False)
        self.data_mask = getattr(config, 'data_mask', False)
        self.lat = None
        self.long = None


class DataSourceInterface:
    def fetch_data(self, settings):
        """Interface method to be overridden by concrete data source handlers."""
        raise NotImplementedError


class DataSourceFactory:
    @staticmethod
    def get_data_source(source_type):
        if source_type == "DEM":
            return DEMDataSource()
        elif source_type == "SLGA":
            return SLGADataSource()
        else:
            raise ValueError(f"Unknown data source: {source_type}")


class DEMDataSource(DataSourceInterface):
    def fetch_data(self, settings):
        try:
            dem_data = dem_harvest.get_dem_layers(
                property_name=settings.property_name,
                layernames=settings.target_sources['DEM'],
                bbox=settings.bbox,
                outpath=settings.outpath
            )
            return dem_data
        except Exception as e:
            print(f"Error fetching DEM data: {e}")
            return []


class SLGADataSource(DataSourceInterface):
    def fetch_data(self, settings):
        print("Fetching SLGA data...")
        # Similar structure as DEM, adapted for SLGA
        try:
            depth_min = []
            depth_max = []
            for layername in settings.target_sources["SLGA"].keys():
                depth_bounds = settings.target_sources["SLGA"][layername]
                dmin, dmax = identifier2depthbounds(depth_bounds)
                depth_min.append(dmin)
                depth_max.append(dmax)

            files_slga = slga_harvest.get_slga_layers(
                property_name=settings.property_name,
                layernames=list(settings.target_sources["SLGA"].keys()),
                bbox=settings.bbox,
                outpath=settings.outpath,
                depth_min=depth_min,
                depth_max=depth_max,
                get_ci=False  # Example flag, should be configured via settings if possible
            )
            return files_slga
        except Exception as e:
            print(f"Error fetching SLGA data: {e}")
            return []



class DataHarvester:
    def __init__(self, path_to_config, input_geom):
        config = load_settings(path_to_config)
        self.settings = Settings(config)
        self.input_geom = input_geom

        self.data_sources = {key: DataSourceFactory.get_data_source(key) for key in self.settings.target_sources}

    def run(self):
        if self.settings.add_buffer:
            self.input_geom = self.input_geom.buffer(0.002, join_style=2, resolution=15)

        for source_name, source in self.data_sources.items():
            try:
                print(f"processing {source_name}:")
                source.fetch_data(self.settings)
            except Exception as e:
                print(f"error fetching {source_name}: {e}")

        if self.settings.data_mask:
            print(f"Masking data in {self.settings.outpath}")
            self.mask_data()

    def mask_data(self):
        tif_files = [f for f in os.listdir(self.settings.outpath)
                     if f.endswith(".tiff")
                     and not f.endswith(("_masked.tiff", "_colored.tiff", "_cog.tiff", "_cog.public.tiff"))]

        for tif in tif_files:
            reproj_mask(
                filename=tif, 
                input_filepath=self.settings.outpath, 
                bbox=self.input_geom,
                crscode=self.settings.target_crs, 
                output_filepath=self.settings.outpath, 
                resample=self.settings.resample)