#!/bin/bash
set -euxo pipefail

mkdir -vp deploy/mongo-data/data{1,2,3}
docker-compose up -d
