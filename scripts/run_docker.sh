#!/bin/bash
#
# run the docker image of the homework checker in a new container.
# The following env vars must be defined
# 
# CHECKER_DATA_DIR=$HOME/checker_data \
# SPARK_PKEY_PATH=/data/data/96224/spark_key \ <<--- in the container file system
# CLUSTER_NAME=spark96224 \
# ./run_docker.sh server

# LIVY_PASS is deprecated.

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
	       --env SPARK_CLUSTER_NAME=$CLUSTER_NAME \
	       --env SPARK_PKEY_PATH=$SPARK_PKEY_PATH \
	       --env LIVY_PASS="%Qq12345678"\
         -p80:8000 \
	       --restart unless-stopped \
             $IMAGE
