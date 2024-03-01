FROM ghcr.io/lambgeo/lambda-gdal:3.6 as gdal

ARG PYTHON_VERSION=3.10  # Default to Python 3.10 if not specified

FROM public.ecr.aws/lambda/python:${PYTHON_VERSION}

# Bring C libs from lambgeo/lambda-gdal image
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

RUN yum install -y gcc gcc-c++ && yum clean all && rm -rf /var/cache/yum /var/lib/yum/history

# Install Jupyter dependencies
RUN pip install jupyterlab notebook jupyterhub nbclassic

COPY requirements-jupyter.txt ${LAMBDA_TASK_ROOT}/requirements.txt

# Upgrade pip and Install Python packages
# Use --no-cache-dir to avoid storing cache, and --prefer-binary to prefer older binary packages over newer source distributions
RUN pip install --upgrade pip
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY notebooks/ ${LAMBDA_TASK_ROOT}/notebooks

# Default port for Jupyter
EXPOSE 8888

# Set ENTRYPOINT to sleep indefinitely
# This is to keep the container running and bypasses the default Lambda behavior
ENTRYPOINT ["sh", "-c", "sleep infinity"]