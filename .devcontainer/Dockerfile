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

# data visualization
RUN pip install seaborn plotly matplotlib plotly_express

# geospatial packages
RUN pip install fiona shapely geopandas rasterio geemap folium leafmap earthengine-api sentinelhub

# experimental
RUN pip install pystac pystac_client stackstac mapboxgl

