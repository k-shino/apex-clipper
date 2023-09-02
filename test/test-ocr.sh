#!/bin/bash

set -eux

cd ../src

docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

export target=2023-08-26_16-44-31
export mode=ocr
export audio=0
export expected_result=0
export debug=false
export skipimage=true

./test-action.sh

# export target=switch2
# export mode=ocr
# export audio=0
# export expected_result=0
# export debug=true

# ./test-action.sh


# export target=switch
# export mode=ocr
# export audio=0
# export expected_result=2
# export debug=true

# ./test-action.sh

