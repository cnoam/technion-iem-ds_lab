#!/bin/bash
#
# run the docker image of the homework checker in a new container.
# The env var CHECKER_DATA_DIR must be defined and contain the full path to the data directory
# e.g.
# CHECKER_DATA_DIR=$HOME/checker_data ./run_docker.sh server

IMAGE=$1
set -u
set +e
mkdir -p $CHECKER_DATA_DIR/logs
chmod  777 $CHECKER_DATA_DIR/logs
set -e
export LIVY_PASS="%Qq12345678"

# Use docker compose since we want to have Redis container for the Spark jobs
if [ -n $IMAGE ]; then
  echo ">>>> The argument $IMAGE is ignored!"
fi
docker-compose up --detach
# docker run -d --mount type=bind,source=$CHECKER_DATA_DIR,target=/data,readonly \
# 	       --mount type=bind,source=$CHECKER_DATA_DIR/logs,target=/logs\
#	       --env CHECKER_DATA_DIR=/data \
#	       --env CHECKER_LOG_DIR=/logs \
#	       --env SPARK_CLUSTER_NAME=noam-spark \
#         --env LIVY_PASS="%Qq12345678"\
#         -p80:8000 \
#	       --restart unless-stopped \
#             $IMAGE
