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

RUN yum install -y gcc gcc-c++ && \
    yum clean all && \
    rm -rf /var/cache/yum /var/lib/yum/history

# Install Jupyter dependencies
RUN pip install jupyter nbconvert ipykernel

# Copy the Datadog Lambda Extension
COPY --from=public.ecr.aws/datadog/lambda-extension:latest /opt/extensions/ /opt/extensions

# Copy requirements and install Python dependencies
COPY requirements-jupyter.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements-jupyter.txt -t ${LAMBDA_TASK_ROOT}

# Install local Python packages
COPY packages/ ${LAMBDA_TASK_ROOT}/packages
COPY requirements-custom.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements-custom.txt -t ${LAMBDA_TASK_ROOT}

# Copy your Lambda function code and notebooks into the container
COPY lambdas/notebook-executor/app/ ${LAMBDA_TASK_ROOT}/app
COPY notebooks/ ${LAMBDA_TASK_ROOT}/notebooks

CMD ["datadog_lambda.handler.handler"]
