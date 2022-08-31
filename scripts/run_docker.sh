#!/bin/bash
#
# run the docker image of the homework checker in a new container.
# The following env vars must be defined
# 
# CHECKER_DATA_DIR=$HOME/checker_data \
# SPARK_PKEY_PATH=/data/data/96224/spark_key \ <<--- in the container file system
# CLUSTER_NAME=spark96224 \
# ./run_docker.sh
#
## sanity check before we go any further
# 
#for v in "CHECKER_LOG_DIR" "CLUSTER_NAME"  "LIVY_PASS"  "SECRET_SIG" "SPARK_PKEY_PATH" "STORAGE_NAME" "GGG"; do
#  echo $v = ${$v}
#  if [ -z "${$v}" ]; then
#    echo missing env var $v
#    exit 1
#  fi
#done

mkdir -p $CHECKER_DATA_DIR/logs
chmod  777 $CHECKER_DATA_DIR/logs

docker-compose up -d
