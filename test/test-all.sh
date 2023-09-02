#!/bin/bash

set -eux

cd ../src

docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

export target=2023-08-26_16-44-31
export mode=all
export audio=0
export expected_result=1

./test-action.sh
