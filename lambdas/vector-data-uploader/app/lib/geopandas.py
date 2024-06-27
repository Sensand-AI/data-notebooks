import os
import json
import geopandas as gpd
from pathlib import Path

def find_shapefile(directory: str) -> str | None:
    """
    Finds the shapefile in the specified directory.

    Parameters:
    - directory (str): The path to the directory to search for the shapefile.

    Returns:
    - str: The path to the shapefile.
    """
    print(f"Searching for shapefile in {directory}")
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".shp"):
                return os.path.join(root, file)

    return None

def get_gdf(path: Path) -> gpd.GeoDataFrame:
    """
    Reads the shapefile at the specified path and returns a GeoDataFrame.

    Parameters:
    - path (Path): The path to the shapefile.

    Returns:
    - gpd.GeoDataFrame: The GeoDataFrame representing the shapefile.
    """
    read_gdf = gpd.read_file(path)
    transformed_gdf = gpd.GeoDataFrame()

    gdf_copy = read_gdf.copy()
    gdf_copy.drop(columns=['geometry'], inplace=True)
    transformed_gdf['metadata'] = gdf_copy.apply(lambda row: json.dumps(row.to_dict()), axis=1)

    transformed_gdf.set_geometry(read_gdf['geometry'], inplace=True)

    return transformed_gdf

