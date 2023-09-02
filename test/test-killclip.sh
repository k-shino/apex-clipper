#!/bin/bash

set -eux

cd ../src

docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

export target=2023-08-26_16-44-31
export mode=kill_clip
export audio=0
export expected_result=1

./test-action.sh


# export target=kill_success
# export mode=kill_clip
# export audio=0
# export expected_result=1

# ./test-action.sh

# export target=kill_failure
# export mode=kill_clip
# export audio=0
# export expected_result=0

# ./test-action.sh

