#!/bin/bash
 IMAGE=$1
 mkdir -p $HOME/data/logs
 docker run -d --mount type=bind,source=$HOME/data,target=/app/data,readonly \
 			  --mount type=bind,source=$HOME/data/logs,target=/logs\
             -p80:8000 \
	     --restart unless-stopped \
             $IMAGE

