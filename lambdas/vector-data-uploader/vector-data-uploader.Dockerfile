FROM 622020772926.dkr.ecr.us-east-1.amazonaws.com/gis-base:latest

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

# Copy the Datadog Lambda Extension
COPY --from=public.ecr.aws/datadog/lambda-extension:latest /opt/. /opt/

WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements and install Python dependencies
# requirements:
# 1. core requirements
# 3. lambda specific requirements
COPY lambdas/vector-data-uploader/requirements.txt ./

# Packages are internal so we need this early
RUN pip install --no-cache-dir -r ./requirements.txt

# Copy your Lambda function code into the container
COPY lambdas/vector-data-uploader/app/ ./app

# Reference the Lambda handler in /app/lambda_function.py
# This is needed for the Datadog Lambda Extension to find the handler
ENV DD_LAMBDA_HANDLER="app.lambda_function.lambda_handler"
# Some datadog specific environment variables
ENV DD_SERVICE="vector-data-uploader"
ENV DD_SERVERLESS_FLUSH_STRATEGY="end"

CMD ["datadog_lambda.handler.handler"]
