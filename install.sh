#!/bin/bash -eux
# Install the needed packages to run the homework checker
# The argument USE_LANG can be {python, spark, cpp, java, xv6}

# this script has to run in the git repo root directory.
USE_LANG=$1


echo Cloning repo of per-course code and data
git clone https://github.com/cnoam/technion_checker_data.git checker_data

echo Installing Checker on ubuntu flavoured machine
sudo apt-get update -y && sudo apt-get upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh
sudo apt install -y docker-compose
mkdir -p ./data/logs

# Before using docker commands, you need to add yourself to the docker group:
set +e
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# set the docker daemon to enabled so it starts on boot
sudo systemctl enable docker
set -e
echo "commit_id='$(git rev-parse --short HEAD)'" > version.py
# Currently need to manually build the dependency images
case $USE_LANG in
   python|spark)
   docker build -t python_base -f Dockerfile_py_base .
   docker tag python_base:latest server
   cd scripts && source ./declare_env && ln -s docker-compose_spark.yml compose.yml
   ;;

   cpp)
   docker build -t server_cpp -f Dockerfile_cpp .
   exit 2 # need to prepare the right compose file
   ;;

   java)
   docker build -t py_java -f Dockerfile_py_java .
   exit 2 # need to prepare the right compose file
   ;;

   xv6)
   docker build -t python_base -f Dockerfile_py_base .
   docker build -t server_xv6 -f Dockerfile_xv6 .
   ln -s docker-compose_xv6.yml scripts/compose.yml
   ;;


   *)
   echo bad argument value.
   exit 1
esac



# TODO: add log rotation (to the disk will not be filled)
# https://docs.docker.com/config/containers/logging/configure/#configure-the-default-logging-driver

echo Adding path to checker_data to .bashrc
echo export CHECKER_DATA_DIR=`pwd`/checker_data >> ~/.bashrc
export CHECKER_DATA_DIR=`pwd`/checker_data
mkdir -p $CHECKER_DATA_DIR/logs
chmod  777 $CHECKER_DATA_DIR/logs

echo "DONE."
cd scripts && docker compose up -d
