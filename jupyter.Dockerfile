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

# Install required packages
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt