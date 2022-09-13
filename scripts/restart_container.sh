#!/bin/bash

# using 'restart' will keep using the old image. This is bad when we want to get the new one
docker-compose down
docker-compose up -d

