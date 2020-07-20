#!/bin/bash
set -euxo pipefail

mkdir -vp deploy/mongo-data/data{1,2,3}
DOCKER_MONGO_PUBLIC_ADDR=$(curl http://checkip.amazonaws.com) docker-compose up -d
