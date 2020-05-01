#!/bin/bash
# try to kill running container
docker kill `docker ps -q` 2>&1 /dev/null
./run_docker.sh server
