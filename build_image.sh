#!/bin/bash

docker buildx use default

docker build . --file Dockerfile --tag logger
