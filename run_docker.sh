#!/bin/bash
 IMAGE=$1
 docker run --mount type=bind,source=$HOME/data,target=/app/data,readonly \
             -p80:8000 \
             --user nobody \
             $IMAGE



