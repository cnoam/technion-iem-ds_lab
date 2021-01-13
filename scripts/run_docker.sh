#!/bin/bash
 IMAGE=$1
 mkdir -p $HOME/checker/data/{db,logs}
 chmod -R 777 $HOME/checker/data/{db,logs}

 docker run -d --mount type=bind,source=$HOME/checker/data,target=/data,readonly \
 	       --mount type=bind,source=$HOME/checker/data/logs,target=/logs\
	       --mount type=bind,source=$HOME/checker/data/db,target=/db\
             -p80:8000 \
	     --user nobody \
	     --restart unless-stopped \
             $IMAGE

