FROM 622020772926.dkr.ecr.us-east-1.amazonaws.com/gis-base:latest

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements-jupyter.txt .
RUN pip install --no-cache-dir -r requirements-jupyter.txt 

COPY packages/ ./packages
COPY requirements-custom.txt .
RUN pip install --no-cache-dir -r requirements-custom.txt 

RUN pip install pytest

ENTRYPOINT [ "pytest", "./packages", "-s" ]
# ENTRYPOINT ["/bin/sh"]

# CMD ["bash", "-c", "sleep infinity"]