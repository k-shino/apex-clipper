#!/bin/bash

set -eux

export tmpdir=${tmpdir:-tmp}

cd ../src

docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

export target=2023-09-29_22-11-45
export mode=kill_clip
export audio=1
export expected_result=1
export debug=true
export dryrun=false
export clean=false

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

