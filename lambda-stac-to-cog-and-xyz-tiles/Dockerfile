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

ARG LAMBDA_TASK_ROOT="/var/task"

COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt -t ${LAMBDA_TASK_ROOT}

COPY handler.py ${LAMBDA_TASK_ROOT}/handler.py

CMD ["handler.lambda_handler"]