#!/bin/bash

set -euo pipefail

aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 948263829143.dkr.ecr.ap-southeast-2.amazonaws.com

docker build -t geo-to-cog:latest . --platform linux/amd64
docker tag geo-to-cog:latest 948263829143.dkr.ecr.ap-southeast-2.amazonaws.com/geo-to-cog:latest
docker push 948263829143.dkr.ecr.ap-southeast-2.amazonaws.com/geo-to-cog:latest

aws lambda update-function-code --function-name geo-to-cog --image-uri 948263829143.dkr.ecr.ap-southeast-2.amazonaws.com/geo-to-cog:latest --region ap-southeast-2