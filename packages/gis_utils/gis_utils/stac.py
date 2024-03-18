import logging
import os
import sys

import pystac_client
import rasterio
from rasterio.windows import from_bounds

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_stac_client(stac_url):
    """
    Initialize and return a STAC client for a given STAC API URL.
    
    Parameters:
    - stac_url (str): The URL of the STAC API.
    
    Returns:
    - A pystac_client.Client object
    """
    try:
        logger.info(f"Initializing STAC client for URL: {stac_url}")
        client = pystac_client.Client.open(stac_url)
        logger.info("STAC client initialized successfully")
        return client
    except Exception:
        logger.error(f"Failed to initialize STAC client for URL: {stac_url}", exc_info=True)
        raise


def query_stac_api(client, bbox, collections, start_date=None, end_date=None, limit=10):
    """
    Query a STAC API for items within a bounding box and date range for specific collections.
    
    Parameters:
    - client: The STAC client initialized with `initialize_stac_client`.
    - bbox (list): The bounding box for the query [min_lon, min_lat, max_lon, max_lat].
    - collections (list): A list of collection IDs to include in the query.
    - start_date (str, optional): The start date for the query (YYYY-MM-DD). Defaults to None.
    - end_date (str, optional): The end date for the query (YYYY-MM-DD). Defaults to None.
    - limit (int): Maximum number of items to return.
    
    Returns:
    - A list of STAC Items that match the query parameters.
    """
    try: 
        search_params = {
            "bbox": bbox,
            "collections": collections,
            "limit": limit
        }
        if start_date and end_date:
            search_params["datetime"] = f"{start_date}/{end_date}"
        
        search = client.search(**search_params)
        items = list(search.items())
        logger.info(f"Found {len(items)} items")
        return items
    except Exception:
        logger.error("Failed to query STAC API", exc_info=True)
        raise

def inspect_stac_item(item):
    """
    Inspects a STAC item and prints out key information to help identify the data type.

    This function iterates over the assets of a given STAC item, printing details such as the
    asset's title, description, media type, and roles. These details can provide insights into
    the nature of the data contained within the item, such as whether it includes satellite imagery,
    elevation data, or other geospatial resources.

    Parameters:
    - item: A STAC item object. This object should conform to the STAC item specification and
            include properties like an ID, datetime, and a dictionary of assets.

    Returns:
    - None: This function does not return any value. It only prints information to the console.
    """

    # Print the unique identifier of the STAC item
    print("Item ID:", item.id)

    # Print the acquisition date of the data, which is stored in the item's properties
    print("Date:", item.properties.get('datetime'))

    # Begin iterating over the assets associated with this STAC item.
    # Assets represent individual data files or resources related to this item.
    print("Assets:")
    for asset_key, asset in item.assets.items():
        # asset_key is the name used to refer to this asset in the STAC item's assets dictionary.
        # asset is the actual asset object, which contains metadata about the data file or resource.

        # Print the key of the asset and its title. The title is a human-readable name for the asset.
        # If no title is provided, it defaults to 'No title'.
        print(f"  - {asset_key}: {asset.title or 'No title'}")

        # Print a description of the asset, which can provide more context about the data it contains.
        # If no description is provided, it defaults to 'No description'.
        print(f"    Description: {asset.description or 'No description'}")
        
        # Print the media type of the asset, which indicates the format of the data file (e.g., 'image/tiff' for a GeoTIFF file).
        print(f"    Media Type: {asset.media_type}")
        
        # Print the roles associated with this asset. Roles are used to describe the function of the asset,
        # such as whether it's the primary data ('data'), metadata about the item ('metadata'), a thumbnail image ('thumbnail'), etc.
        # The roles are joined by a comma in case there are multiple roles.
        print(f"    Roles: {', '.join(asset.roles)}")

def process_dem_asset(dem_asset, bbox, output_tiff_filename):
    """
    Process a DEM asset by reading a specific region defined by a bounding box and writing it to a new file.

    Parameters:
    - dem_asset: The STAC asset object containing the href to the DEM file.
    - bbox (tuple): The bounding box for the region to extract (min_lon, min_lat, max_lon, max_lat).
    - output_tiff_filename (str): The file path where the output TIFF file will be written.

    Returns:
    - None
    """
    try:
        logger.info("Opening DEM asset from: %s", dem_asset.href)
        data, metadata = None, {}

        with rasterio.open(dem_asset.href) as src:
            window = from_bounds(*bbox, transform=src.transform)
            data = src.read(window=window)

            # Extract required metadata or other information from src
            metadata = src.meta.copy()
            metadata.update({
                'height': window.height,
                'width': window.width,
                'transform': rasterio.windows.transform(window, src.transform)
            })
            logger.info("Writing to file:  %s", output_tiff_filename)
            with rasterio.open(output_tiff_filename, 'w', **metadata) as dst:
                dst.write(data)
                logger.info("Written data to %s", output_tiff_filename)

            # Calculate the size of the data in bytes
            data_size_bytes = data.nbytes
            logger.info("Read data size: %d bytes", data_size_bytes)

            # Optionally, log the size of the written file
            output_file_size = os.path.getsize(output_tiff_filename)
            logger.info("Output file size: %d bytes", output_file_size)

        return data, metadata, src
    except Exception as e:
        logger.error("Failed to process DEM asset: %s", e, exc_info=True)
        raise