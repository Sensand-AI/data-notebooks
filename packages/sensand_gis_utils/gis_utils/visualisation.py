import logging
import os
import sys
import json
import numpy as np 
import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform #reproject, Resampling
from rasterio.plot import reshape_as_raster
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from matplotlib import cm
from matplotlib.colors import Normalize

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


def get_coords_from_geodataframe(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


def colour_geotiff_and_save_cog(input_geotiff, colour_map):
    
    output_colored_tiff_filename = input_geotiff.replace('.tif', '_colored.tif')
    output_cog_filename = input_geotiff.replace('.tif', '_cog.public.tif')
    
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