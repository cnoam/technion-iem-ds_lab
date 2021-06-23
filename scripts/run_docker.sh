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
 docker run -d --mount type=bind,source=$CHECKER_DATA_DIR,target=/data,readonly \
 	       --mount type=bind,source=$CHECKER_DATA_DIR/logs,target=/logs\
	       --env CHECKER_DATA_DIR=/data \
	       --env CHECKER_LOG_DIR=/logs \
         -p80:8000 \
	       --restart unless-stopped \
             $IMAGE
