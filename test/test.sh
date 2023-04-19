#!/bin/bash

set -eux

cd ../src

docker build -f ./docker/Dockerfile -t kshino/apex-clipper:m1 .

cd ../test

# rm -rf ocr out work apex_kill_clip
# mkdir -p ocr out work apex_kill_clip

docker-compose -f apex_tracker.yml up