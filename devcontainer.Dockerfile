FROM mcr.microsoft.com/vscode/devcontainers/python:3.10-bullseye

RUN apt-get update && apt-get install -y \
		gcc libgdal-dev gdal-bin libpq-dev postgresql-client\
		&& rm -rf /var/lib/apt/lists/*

ENV GDAL_CONFIG=/usr/bin/gdal-config

WORKDIR /workspace

RUN pip install --upgrade pip

# Copy dependencies and install them
COPY requirements-core.txt /workspace/requirements-core.txt
COPY requirements-jupyter.txt /workspace/requirements-jupyter.txt
COPY requirements-dev.txt /workspace/requirements-dev.txt

RUN cat /workspace/requirements-core.txt /workspace/requirements-jupyter.txt /workspace/requirements-dev.txt > /workspace/requirements.txt

RUN pip install -r /workspace/requirements.txt

# Copy startup script and install custom extensions in editable mode
COPY requirements-custom.txt /workspace/requirements-custom.txt
COPY packages /workspace/packages

RUN pip install -r /workspace/requirements-custom.txt

CMD ["sleep", "infinity"]