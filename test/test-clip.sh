#!/bin/bash

set -eux

export tmpdir=${tmpdir:-tmp}

cd ../src

docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

# export target=clip
# export mode=match_clip
# export audio=0
# export expected_result=1

# ./test-action.sh

# export target=switch
# export mode=match_clip
# export audio=0
# export expected_result=2

# ./test-action.sh


export target=2023-08-26_16-44-31
export mode=match_clip
export audio=0
export expected_result=2
export debug=true

./test-action.sh
