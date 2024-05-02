FROM --platform=linux/amd64 debian:bullseye-slim

WORKDIR /

RUN apt-get update && apt-get install -y \
  awscli \
  jq \
  && rm -rf /var/lib/apt/lists/*