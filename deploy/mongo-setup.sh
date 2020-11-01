#!/bin/bash
set -euxo pipefail

MONGODB1=mongodb-run-tests-rs1
MONGODB2=mongodb-run-tests-rs2
MONGODB3=mongodb-run-tests-rs3
IMAGE=docker.io/library/mongo:4.0.19-xenial

podman stop -i ${MONGODB1} ${MONGODB2} ${MONGODB3}
podman rm -i ${MONGODB1} ${MONGODB2} ${MONGODB3}
podman run -d --name ${MONGODB1} -p 27017:27017 ${IMAGE} --replSet rsdacot
podman run -d --name ${MONGODB2} -p 27018:27017 ${IMAGE} --replSet rsdacot
podman run -d --name ${MONGODB3} -p 27019:27017 ${IMAGE} --replSet rsdacot

echo "Waiting for startup.."
sleep 10

echo SETUP.sh time now: `date +"%T" `
mongo --host ${MONGODB_PUBLIC_ADDR}:27017 <<EOF
var cfg = {
    "_id": "rsdacot",
    "protocolVersion": 1,
    "version": 1,
    "members": [
        {
            "_id": 0,
            "host": "${MONGODB_PUBLIC_ADDR}:27017",
            "priority": 2
        },
        {
            "_id": 1,
            "host": "${MONGODB_PUBLIC_ADDR}:27018",
            "priority": 0
        },
        {
            "_id": 2,
            "host": "${MONGODB_PUBLIC_ADDR}:27019",
            "priority": 0
        }
    ],
    "settings": {
        "chainingAllowed": true
    }
};
rs.initiate(cfg, { force: true });
rs.reconfig(cfg, { force: true });
rs.slaveOk();
db.getMongo().setReadPref('nearest');
db.getMongo().setSlaveOk(); 
EOF
