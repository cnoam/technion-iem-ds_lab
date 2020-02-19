#!/usr/bin/env bash
time docker build -t server .. && ./restart_container.sh
