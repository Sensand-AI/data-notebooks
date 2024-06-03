FROM 622020772926.dkr.ecr.us-east-1.amazonaws.com/gis-base:latest

# COPY requirements-jupyter.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements-jupyter.txt -t ${LAMBDA_TASK_ROOT}

# COPY packages/ ${LAMBDA_TASK_ROOT}/packages
# COPY requirements-custom.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements-custom.txt -t ${LAMBDA_TASK_ROOT}

RUN pip install pytest