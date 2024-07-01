import os
import json
import logging
import geopandas as gpd
from sqlalchemy import engine
from sqlalchemy.dialects.postgresql import JSONB
from pathlib import Path

TABLE_NAME = 'vector_data'

logger = logging.getLogger("VectorDataUploader")
logger.setLevel(logging.INFO)

def find_shapefile(directory: Path) -> str | None:
    """
    Finds the shapefile in the specified directory.

    Parameters:
    - directory (str): The path to the directory to search for the shapefile.

    Returns:
    - str: The path to the shapefile.
    """
    logger.info(f"Searching for shapefile in {directory}")
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".shp"):
                return os.path.join(root, file)

    return None

def get_gdf(path: str) -> gpd.GeoDataFrame:
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

def write_to_postgis(gdf: gpd.GeoDataFrame, engine: engine.Engine):
    """
    Writes the GeoDataFrame to a PostGIS table.

    Parameters:
    - gdf (gpd.GeoDataFrame): The GeoDataFrame to write to the table.
    - table_name (str): The name of the table to write to.
    - connection_string (str): The connection string to the PostGIS database.
    """

    gdf.to_postgis(TABLE_NAME, engine, if_exists="append", index=True, dtype={"metadata": JSONB})

