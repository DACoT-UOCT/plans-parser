#!/bin/bash
set -euxo pipefail

AWS_VM_ADDR=$(curl http://checkip.amazonaws.com)
mkdir -vp deploy/mongo-data/data{1,2,3}
MONGO_URI="mongodb://${AWS_VM_ADDR}:30001,${AWS_VM_ADDR}:30002,${AWS_VM_ADDR}:30003/?replicaset=rsuoct" DOCKER_MONGO_PUBLIC_ADDR=${AWS_VM_ADDR} docker-compose up -d
