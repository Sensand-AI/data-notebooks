FROM jupyter/datascience-notebook

# Install GDAL dependencies
USER root
RUN apt-get update && apt-get install -y \
    libgdal-dev \
    gdal-bin

# Set environment variable for GDAL
ENV GDAL_CONFIG=/usr/bin/gdal-config

# Switch back to the jovyan user
USER jovyan

# Install core python packages
RUN pip install numpy pandas boto3 tornado

# data visualizationPP
RUN pip install seaborn plotly matplotlib plotly_express hvplot

# geospatial packages
RUN pip install fiona shapely geopandas rasterio[s3] gdal2tiles earthengine-api sentinelhub

# mapping packages
# simplify to remove extra packages later on e.g. leafmap
RUN pip install folium leafmap xarray_leaflet jupyter-server-proxy localtileserver mapboxgl ipyleaflet

# stac packages
RUN pip install pystac pystac_client odc-stac stackstac[viz]

# experimental
RUN pip install dask-geopandas rioxarray sidecar mapclassify panel

# temporarily removed packages:
# 