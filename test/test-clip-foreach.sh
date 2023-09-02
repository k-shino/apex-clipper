#!/bin/bash

set -eux

cd ../src

docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

# # clip.mp4のクリップ作成

# export target=clip
# export mode=match_clip_foreach
# export audio=0
# export expected_result=1

# ./test-action.sh

# # switch.mp4のクリップ作成

# export target=switch
# export mode=match_clip_foreach
# export audio=0
# export expected_result=2

# ./test-action.sh

# OCR中フォルダへのクリップ作成

# export target=switch
# export mode=match_clip_foreach
# export audio=0
# export expected_result=2
# export ocr_in_progress=true

# ./test-action.sh

export target=2023-08-26_16-44-31
export mode=match_clip_foreach
export audio=1
export expected_result=2
export debug=false

./test-action.sh
