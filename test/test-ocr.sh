#!/bin/bash

set -eux

export tmpdir=${tmpdir:-tmp}

cd ../src

docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

export target=2023-09-15_23-54-03
export mode=ocr
export audio=0
export expected_result=0
export debug=false
export skipimage=false

./test-action.sh

# export target=2023-08-26_16-44-31
# export mode=ocr
# export audio=0
# export expected_result=0
# export debug=false
# export skipimage=false

# ./test-action.sh

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

