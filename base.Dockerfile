FROM ghcr.io/lambgeo/lambda-gdal:3.6 as gdal

FROM public.ecr.aws/lambda/python:3.10

# Install some system dependencies
RUN yum install -y gcc gcc-c++ unzip && \
    yum clean all && \
    rm -rf /var/cache/yum /var/lib/yum/history

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

# Install core packages
COPY requirements-core.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements-core.txt -t ${LAMBDA_TASK_ROOT}

# docker build -f base.Dockerfile -t 622020772926.dkr.ecr.us-east-1.amazonaws.com/gis-base:latest . --platform linux/amd64
# docker run --name cmd-binbash-test -d 622020772926.dkr.ecr.us-east-1.amazonaws.com/gis-base:latest
# docker tag gis-base:latest 622020772926.dkr.ecr.us-east-1.amazonaws.com/gis-base:latest
# docker push 622020772926.dkr.ecr.us-east-1.amazonaws.com/gis-base:latest