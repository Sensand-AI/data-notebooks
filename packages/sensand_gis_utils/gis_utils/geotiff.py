import json
import logging
from typing import Any, Dict, Tuple

import numpy as np
import rasterio
from matplotlib import cm
from matplotlib.colors import Normalize
from rasterio.io import DatasetReader
from rasterio.plot import reshape_as_raster
from rasterio.warp import calculate_default_transform

# Initialize the logger for this module
logger = logging.getLogger(__name__)


def apply_color_map(tif_data: np.ndarray, color_map: str, meta: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Apply a color map to the TIFF data and update the metadata to reflect changes.
    
    Args:
        tif_data (np.ndarray): The raw TIFF data.
        color_map (str): The name of the color map to apply.
        meta (Dict[str, Any]): The metadata dictionary that will be updated.

    Returns:
        Tuple[np.ndarray, Dict[str, Any]]: A tuple containing the colored data and updated metadata.
    """
    cmap = cm.get_cmap(color_map)  # Using Matplotlib to get the color map
    # Remove NaN values from the data
    na = tif_data[~np.isnan(tif_data)]
    # Get the minimum and maximum values from the data
    norm = Normalize(vmin=min(na), vmax=max(na))
    # Apply the color map to the data
    # The [:, :, :3] is used to remove the alpha channel from the color map
    # The * 255 is used to scale the values to the range [0, 255]
    # And we do the usual dev thing of assuming the data is uint8
    colored_data = (cmap(norm(tif_data))[:, :, :3] * 255).astype(np.uint8)
    
    # Update the metadata to reflect the change in band count (assumes RGB output)
    # Make a copy to avoid mutating the original meta directly
    updated_meta = meta.copy()
    # Update the count to 3 for RGB
    updated_meta.update({"count": 3})

    return colored_data, updated_meta

def load_and_transform_geotiff(input_geotiff: str) -> Tuple[Dict[str, Any], DatasetReader]:
    """
    Load metadata from a GeoTIFF file and transform it to a new CRS.
    Specifically, EPSG:4326 because that's what we're using for the web map.
    """
    with rasterio.open(input_geotiff) as src:
        meta = src.meta.copy()
        # Consider making the CRS configurable
        dst_crs = rasterio.crs.CRS.from_epsg(4326)
        # Determine how to transform the source CRS to the destination CRS
				# so that they correctly represent their intended geographical locations
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        meta.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height,
        })
       # Optionally read data if it will be used immediately or transform is needed
        data = src.read(1, masked=True)  # Reading only the first band as example
    return meta, data

def write_colored_geotiff(colored_data: np.ndarray, meta: Dict[str, Any], filename: str) -> None:
    """Write the colored GeoTIFF to a file."""
    # Reshape the colored data to match raster format
    raster_data = reshape_as_raster(colored_data)
    with rasterio.open(filename, 'w', **meta) as dst:
        for i in range(meta['count']):  # Assuming RGB data
            dst.write(raster_data[i], i+1)