# docker build -f gis.Dockerfile -t nogdal .

FROM python:3.10-bullseye AS compile-image

RUN apt-get update && apt-get install -y \
		gcc libgdal-dev gdal-bin \
		&& rm -rf /var/lib/apt/lists/*

ENV GDAL_CONFIG=/usr/bin/gdal-config

COPY requirements-jupyter.txt .
RUN pip install --no-cache-dir -r requirements-jupyter.txt

COPY packages/ ./packages
COPY requirements-custom.txt .
RUN pip install --no-cache-dir -r requirements-custom.txt


FROM python:3.10-bullseye AS build-image

RUN apt-get update && apt-get install -y \
		gdal-bin \
		&& rm -rf /var/lib/apt/lists/*

ENV GDAL_CONFIG=/usr/bin/gdal-config

COPY --from=compile-image /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=compile-image /usr/local/bin /usr/local/bin

CMD [ "sleep", "infinity" ]
