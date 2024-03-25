FROM ghcr.io/lambgeo/lambda-gdal:3.6 as gdal

FROM public.ecr.aws/aws-cli/aws-cli as aws-cli

FROM public.ecr.aws/lambda/python:3.10

ARG \
    AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-"us-east-1"} \
    AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-""} \
    AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-""} \
    AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN:-""}

ENV \
    AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} \
    AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}

# Install aws-cli
COPY --link --from=aws-cli /usr/local/aws-cli/ /usr/local/aws-cli/
COPY --link --from=aws-cli /usr/local/bin/ /usr/local/bin

# Copy the Datadog Lambda Extension
COPY --from=public.ecr.aws/datadog/lambda-extension:latest /opt/extensions/ /opt/extensions

# Install some system dependencies
RUN yum install -y gcc gcc-c++ unzip && \
    yum clean all && \
    rm -rf /var/cache/yum /var/lib/yum/history

# Install the AWS Lambda extension for AWS Secrets Manager and AWS Systems Manager
RUN curl $(aws lambda get-layer-version-by-arn --arn arn:aws:lambda:us-east-1:177933569100:layer:AWS-Parameters-and-Secrets-Lambda-Extension:11 --query 'Content.Location' --output text) --output layer.zip
RUN unzip layer.zip -d /opt
RUN rm layer.zip

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

# Install Jupyter dependencies
RUN pip install jupyter nbconvert ipykernel

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

# Reference the Lambda handler in /app/lambda_function.py
# This is needed for the Datadog Lambda Extension to find the handler
ENV DD_LAMBDA_HANDLER="app.lambda_function.lambda_handler"

CMD ["datadog_lambda.handler.handler"]
