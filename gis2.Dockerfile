# Stage 1: Use the GDAL image to set up the build environment
FROM ghcr.io/lambgeo/lambda-gdal:3.6 as gdal

# Stage 2: Compile image for building Python dependencies
FROM python:3.10-bullseye as build-image

# Bring C libs from the gdal image
COPY --from=gdal /opt/lib/ /opt/lib/
COPY --from=gdal /opt/include/ /opt/include/
COPY --from=gdal /opt/share/ /opt/share/
COPY --from=gdal /opt/bin/ /opt/bin/
ENV \
  GDAL_DATA=/opt/share/gdal \
  PROJ_LIB=/opt/share/proj \
  GDAL_CONFIG=/opt/bin/gdal-config \
  GEOS_CONFIG=/opt/bin/geos-config \
  PATH=/opt/bin:$PATH

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-jupyter.txt .
RUN pip install --no-cache-dir -r requirements-jupyter.txt

COPY packages/ ./packages
COPY requirements-custom.txt .
RUN pip install --no-cache-dir -r requirements-custom.txt

# Stage 3: Final runtime image
FROM python:3.10-bullseye

# Bring runtime C libs from the gdal image
COPY --from=gdal /opt/lib/ /opt/lib/
COPY --from=gdal /opt/include/ /opt/include/
COPY --from=gdal /opt/share/ /opt/share/
COPY --from=gdal /opt/bin/ /opt/bin/
ENV \
  GDAL_DATA=/opt/share/gdal \
  PROJ_LIB=/opt/share/proj \
  GDAL_CONFIG=/opt/bin/gdal-config \
  GEOS_CONFIG=/opt/bin/geos-config \
  PATH=/opt/bin:$PATH

# Copy installed Python packages from the build image
COPY --from=build-image /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=build-image /usr/local/bin /usr/local/bin


CMD ["sleep", "infinity"]
