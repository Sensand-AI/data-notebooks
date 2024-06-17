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
COPY --from=public.ecr.aws/datadog/lambda-extension:latest /opt/extensions/ /opt/extensions

WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements and install Python dependencies
COPY requirements-jupyter.txt requirements-custom.txt ./
# Packages are internal so we need this early
COPY packages/ ./packages
RUN pip install --no-cache-dir -r ./requirements-jupyter.txt && \
    pip install --no-cache-dir -r ./requirements-custom.txt

# Copy your Lambda function code and notebooks into the container
COPY lambdas/notebook-executor/app/ ./app
COPY notebooks/ ./notebooks

# Reference the Lambda handler in /app/lambda_function.py
# This is needed for the Datadog Lambda Extension to find the handler
ENV DD_LAMBDA_HANDLER="app.lambda_function.lambda_handler"
# Some datadog specific environment variables
ENV DD_SERVICE="notebook-executor"

ENV DD_SERVERLESS_FLUSH_STRATEGY="end"

CMD ["datadog_lambda.handler.handler"]
