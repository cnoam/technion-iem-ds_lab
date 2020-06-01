#!/bin/bash
# try to kill running container
docker kill `docker ps -q` &> /dev/null
./run_docker.sh server
