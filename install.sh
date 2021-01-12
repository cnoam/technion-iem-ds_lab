#!/bin/bash -ex

# this script has to run in the git repo root directory.
echo Installing Checker on ubuntu flavoured machine
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install -y docker.io
mkdir -p ./data/logs

# Before using docker commands, you need to add yourself to the docker group:
set +e
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# set the docker daemon to enabled so it starts on boot
sudo systemctl enable docker
set -e

# Currently need to manually build the dependency images
docker build -t python_cmake_base -f Dockerfile_base .
docker build -t py_java_cpp_base -f Dockerfile_py_java_cpp_base .
docker build -t server .

# TODO: add log rotation (to the disk will not be filled)
# https://docs.docker.com/config/containers/logging/configure/#configure-the-default-logging-driver

echo "DONE."
