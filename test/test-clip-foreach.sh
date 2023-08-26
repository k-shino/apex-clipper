#!/bin/bash

set -eux

cd ../src

docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

export target=clip
export mode=match_clip_foreach
export audio=0
export expected_result=1

./test-action.sh

