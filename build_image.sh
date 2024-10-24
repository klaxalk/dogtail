#!/bin/bash

docker buildx use default

docker build . --file Dockerfile --tag docker_logger
