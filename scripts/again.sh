#!/usr/bin/env bash
docker build -t server .. && ./restart_container.sh
