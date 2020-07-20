#!/bin/bash
set -euxo pipefail

MONGODB1=mongo1
MONGODB2=mongo2
MONGODB3=mongo3
MONGODB_PUBLIC_ADDR=${DOCKER_MONGO_PUBLIC_ADDR}

echo "Waiting for startup.."
sleep 10

echo SETUP.sh time now: `date +"%T" `
mongo --host ${MONGODB1}:27017 <<EOF
var cfg = {
    "_id": "rsuoct",
    "protocolVersion": 1,
    "version": 1,
    "members": [
        {
            "_id": 0,
            "host": "${MONGODB_PUBLIC_ADDR}:30001",
            "priority": 2
        },
        {
            "_id": 1,
            "host": "${MONGODB_PUBLIC_ADDR}:30002",
            "priority": 0
        },
        {
            "_id": 2,
            "host": "${MONGODB_PUBLIC_ADDR}:30003",
            "priority": 0
        }
    ],settings: {chainingAllowed: true}
};
rs.initiate(cfg, { force: true });
rs.reconfig(cfg, { force: true });
rs.slaveOk();
db.getMongo().setReadPref('nearest');
db.getMongo().setSlaveOk(); 
EOF
