#!/bin/bash
set -euxo pipefail

mkdir -vp deploy/mongo-data/data{1,2,3}
docker-compose -e DOCKER_MONGO_PUBLIC_ADDR=$(curl http://checkip.amazonaws.com) up -d
