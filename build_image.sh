#!/bin/bash

docker buildx use default

docker build . --file Dockerfile --tag klaxalk/docker_logger:1.0.0 --tag klaxalk/docker_logger:latest --platform amd64 --push
