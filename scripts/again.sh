#!/usr/bin/env bash

# save the commit ID into a file, so it can be used within the docker container
echo "commit_id='$(git rev-parse --short HEAD)'" > ../version.py
docker build -t server .. && ./restart_container.sh
