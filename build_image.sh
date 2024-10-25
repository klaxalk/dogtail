#!/bin/bash

docker buildx use default

docker build . --file Dockerfile --tag klaxalk/dogtail:1.0.0 --tag klaxalk/dogtail:latest --platform amd64
