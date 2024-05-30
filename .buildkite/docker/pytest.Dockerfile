FROM python:3.10-bullseye

RUN apt-get update && apt-get install -y \
		gcc libgdal-dev gdal-bin \
		&& rm -rf /var/lib/apt/lists/*

ENV GDAL_CONFIG=/usr/bin/gdal-config

COPY requirements-jupyter.txt .
RUN pip install --no-cache-dir -r requirements-jupyter.txt

COPY packages/ ./packages
COPY requirements-custom.txt .
RUN pip install --no-cache-dir -r requirements-custom.txt

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

CMD [ "pytest", "-s" ]