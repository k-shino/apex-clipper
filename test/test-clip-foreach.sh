#!/bin/bash

set -eux

cd ../src

docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

# # ocr
# rm -rf ocr
# mkdir -p ocr

# # ffmpeg
rm -rf out work apex_kill_clip
mkdir -p out work apex_kill_clip

docker-compose -f apex_tracker_local_clip_foreach.yml up

# ffmpeg -y -ss 10 -i ./src_movie/dir02/2022-12-30_23-38-24.mkv -t 10 -vcodec libx264 -acodec libmp3lame -vsync 1 -async 1000 -map 0:v:0 -map 0:a:1 -map 0:a:2 -map 0:a:3 work/test2.mp4
# C^CReceived > 3 system signals, hard exiting=00:00:08.54 bitrate=5399.2kbits/s speed=0.0233x
