FROM ghcr.io/lambgeo/lambda-gdal:3.6 as gdal

FROM public.ecr.aws/lambda/python:3.10

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
RUN pip install jupyter nbconvert ipykernel

# Copy requirements.txt and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt -t ${LAMBDA_TASK_ROOT}

# Copy local Python packages
COPY packages/ ${LAMBDA_TASK_ROOT}/packages

# Install local Python packages
RUN pip install ${LAMBDA_TASK_ROOT}/packages/gis_utils/ ${LAMBDA_TASK_ROOT}/packages/aws_utils/

# # Copy your Lambda function code and notebooks into the container
COPY app/ ${LAMBDA_TASK_ROOT}/app
COPY notebooks/ ${LAMBDA_TASK_ROOT}/notebooks

CMD ["app.lambda_function.lambda_handler"]