import os
import json
import numpy as np
import boto3
from botocore.config import Config
from boto3.s3.transfer import TransferConfig
import rasterio
from rasterio.mask import mask
from rasterio.features import geometry_window, geometry_mask
from rasterio.plot import reshape_as_raster
from rasterio.windows import transform
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import geopandas as gpd
import pystac_client
from gdal2tiles import generate_tiles

# Set up S3 and configurations
s3 = boto3.resource('s3')
config = Config(retries={'max_attempts': 10, 'mode': 'standard'})
s3_client = boto3.client('s3', config=config)
multi_part_config = TransferConfig(
    multipart_threshold=1024 * 25, max_concurrency=10,
    multipart_chunksize=1024 * 25, use_threads=True
)

def get_geometry_from_s3(bucket, geom_path):
    """
    Retrieve geometry from a given S3 bucket and path.

    Parameters:
    - bucket: S3 bucket name
    - geom_path: path to the geometry file in the bucket

    Returns:
    - geometry_gdf: GeoDataFrame containing the geometry
    - bbox: bounding box of the geometry
    """
    geom_obj = s3_client.get_object(Bucket=bucket, Key=geom_path)
    geom_content = geom_obj['Body'].read().decode('utf-8')
    geometry_gdf = gpd.read_file(geom_content)  # Read the GeoJSON content with GeoPandas
    bbox = geometry_gdf.geometry.bounds.iloc[0].tolist()
    
    # Ensure there is at least one geometry in the GeoDataFrame
    if not geometry_gdf.empty:
        return geometry_gdf, bbox
    else:
        print("No geometry found in the provided path.")
        return None

def ndvi_to_colored_image(ndvi, cmap=plt.cm.RdYlGn):
    """
    Convert NDVI data to a colored image using a colormap.

    Parameters:
    - ndvi: NDVI data array
    - cmap: colormap to apply to the NDVI data

    Returns:
    - colored_ndvi: Colored NDVI image
    """
    ndvi_norm = (ndvi + 1) / 2.0  # Normalize NDVI values to the range [0, 1]
    colored_ndvi = (cmap(ndvi_norm)[:, :, :3] * 255).astype(np.uint8)  # Apply colormap and convert to [0, 255] range
    return colored_ndvi

def cog_to_xyz_tiles(cog_dir, s3_dir, bucket):
        """
        Take a cog saved in /tmp and create map tiles from it.

        parameters:
        - cog_dir - the local /tmp directory for the cog
        - s3_dir - the name of the parent directory for the tiles to be stored in the S3 bucket
        -zoom - the zoom levels to generate the tiles for

        Returns:
        - XYZ map tiles for the input COG, uploaded to an S3 bucket
        """
    # Create a directory to store the tiles
        temp_dir= '/tmp/stac-tiles'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        generate_tiles(cog_dir, temp_dir, zoom='14-16')
        # Upload the tiles to the S3 bucket directly within the lambda_handler function
        for root, dirs, files in os.walk(temp_dir):
            for filename in files:
                local_path = os.path.join(root, filename)
                relative_path = os.path.relpath(local_path, temp_dir)
                s3_path = os.path.join(s3_dir, relative_path)  # Modify the s3_path to include the parent directory
                s3_client.upload_file(local_path, bucket, s3_path)
                print(f"File {s3_path} uploaded to s3://{bucket}/{s3_path}")

        print(f"XYZ tiles uploaded to s3://{bucket}/{s3_dir}")
        shutil.rmtree(temp_dir)

def lambda_handler(event, context):
    """
    AWS Lambda handler function to process Sentinel-2 data, calculate NDVI,
    apply a colormap, and upload the results to an S3 bucket.
         - greyscale cog containing original NDVI values
         - cog with colormap embedded, for creating map tiles
         - xyz tileset

    This function uses pystac to talk to the online Sentinel-2 COG archive (https://earth-search.aws.element84.com/v1)
    and fetch images that meet the query parameters. 
    - boundary (geojson, but in future postGIS geometry would be preferable)
    - date - at the moment this is hard coded, but it should be modified as needed. 
            This could be set to find the most recently added COG, allowing for new NDVI/ true colour
            images to be generated every 5 days over a given AOI
    - optional parameters like cloud cover, currently set as lt:50%

    A future iteration of this function could build a datacube over a boundary, which could then be used for
    timeseries processing (use case: growth curves for agriculture clients, tracking forest disturbance and recovery)

    Parameters:
    - event: AWS Lambda event data (not used in this example)
    - context: AWS Lambda context data (not used in this example)

    Returns:
    - A dictionary containing the HTTP status code and body content indicating
      the success of the operation.
    """
    bucket = 'jenna-remote-sensing-sandbox' #temp hardcoded bucket
    geom_path = "stac-demo-aoi.geojson"
    dst_crs = 'EPSG:3857'
    timerange = '2023-10-01/2023-10-10' # time range to search for imagery within. This will be replaced with an 'event' trigger when a new sentinel image is added to the AWS collection
    sentinel_search_url = "https://earth-search.aws.element84.com/v1"

    colors = plt.get_cmap('viridis')(np.linspace(0, 1, 256))
    cmap = ListedColormap(colors)

    # Get geometry as a GeoDataFrame
    geometry_gdf, bbox = get_geometry_from_s3(bucket, geom_path)
    print(f"Original Geometry: {geometry_gdf}")

    # Perform STAC filtering to get Sentinel-2 data
    try:
        catalog = pystac_client.Client.open(sentinel_search_url)
        results = catalog.search(
            max_items=2,
            #intersects=json.loads(geometry_gdf.to_json())["features"][0]["geometry"],
            bbox=bbox,
            datetime=timerange,
            query={"eo:cloud_cover": {"lt": 50}},
            collections=["sentinel-2-l2a"]
        ).item_collection()
    except pystac_client.exceptions.APIError as e:
        print(f"Error querying STAC API: {e}")
        return

    for item in results:
        # Process each STAC item and calculate NDVI
        raster_crs = 'epsg:' + str(item.properties['proj:epsg'])
        print("Raster CRS from STAC: {}".format(raster_crs))
        print("Item ID from STAC: {}".format(item.id)) 

        red_href = item.assets['red'].href
        print("RED band href: {}".format(red_href))
        nir_href = item.assets['nir'].href

        polygon_gdf = geometry_gdf.to_crs("EPSG:32755") #This needs to be changed from hardcoded to pulling from the fetched satellite images

        with rasterio.open(nir_href) as nir_src, rasterio.open(red_href) as red_src:
            for feature in polygon_gdf.iterfeatures(show_bbox=True):
                window = geometry_window(nir_src, [feature["geometry"]])
                window_transform = transform(window, nir_src.transform)
                window_shape = (window.height, window.width)

                # Read all the data in the window, masking out any NoData
                nir = nir_src.read(window=window, masked=True).astype('float32')
                red = red_src.read(window=window, masked=True).astype('float32')

                # Update the NoData mask to exclude anything outside the polygon
                mask = geometry_mask([feature["geometry"]], window_shape, window_transform)
                nir.mask += mask
                red.mask += mask

                # Calculate NDVI
                ndvi = (nir - red) / (nir + red)

                # Save the masked NDVI to one tif per polygon
                ndvi_path = '/tmp/stac-ndvi.tif'

                meta = nir_src.meta

                meta.update({"driver": "GTiff", 
                             "dtype": ndvi.dtype, 
                             "height": window.height, 
                             "width":window.width, 
                             "transform": window_transform,
                             "count":1})
                
                with rasterio.open(ndvi_path, 'w', **meta) as dst:
                    dst.write(ndvi)

                ndvi_s3key = 'stac-ndvi.tif'
                s3.meta.client.upload_file(ndvi_path, bucket, ndvi_s3key, Config=multi_part_config)
                print(f"NDVI GeoTIFFs uploaded to s3://{bucket}/{ndvi_s3key}")

        # Read the NDVI data, apply colormap, and save as a new GeoTIFF
        with rasterio.open('/tmp/stac-ndvi.tif') as src:
            ndvi_data = src.read(1, masked=True)
            meta = src.meta.copy()
            colored_image = ndvi_to_colored_image(ndvi_data.filled(np.nan))
            meta.update(dtype=rasterio.uint8, count=3)
            with rasterio.open('/tmp/colored_ndvi.tif', 'w', **meta) as dst:
                dst.write(reshape_as_raster(colored_image))

            # Upload the colored NDVI GeoTIFF to S3
            ndvi_rgb_s3key = 'stac-ndvi-rgb.tif'
            s3.meta.client.upload_file('/tmp/colored_ndvi.tif', bucket, ndvi_rgb_s3key, Config=multi_part_config)
            print(f"Colored NDVI GeoTIFF uploaded to s3://{bucket}/{ndvi_rgb_s3key}")

        # Generate and upload XYZ tiles to S3
        cog_to_xyz_tiles('/tmp/colored_ndvi.tif', 'stac-tiles-ndvi', bucket)     
        cog_to_xyz_tiles('/tmp/stac-vis.tif', 'stac-tiles-rgb', bucket)   

    os.remove(vis_path)
    os.remove(ndvi_path)
    os.remove(ndvi_rgb_path)

    return {
        'statusCode': 200,
        'body': json.dumps('NDVI calculation, COG conversion, and upload successful!')
    }

#comment out when deploying
if __name__ == "__main__":
   lambda_handler({},{})