#!/bin/bash

set -eu

target=${target:-clip}
mode=${mode:-ocr}
audio=${audio:-1}
expected_result=${expected_result:-1}
debug=${debug:-false}

dummy_date="2023-08-01_10-00-00"

# cd ../src

# docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

rm -rf tmp
mkdir -p tmp
cd tmp
mkdir -p orig out ocr work apex_kill_clip
cp "../orig/${target}.mp4" orig/${dummy_date}.mp4

if [ "$mode" == "match_clip" ]|| [ "$mode" == "match_clip_foreach" ] || [ "$mode" == "kill_clip" ]; then
    cp -r "../ocr/${target}" ./ocr/${dummy_date}
fi

cp ../apex_tracker.yml apex_tracker_tmp.yml

sed -i -e "s/<image-tag>/apex-clipper:local/" apex_tracker_tmp.yml
sed -i -e "s/<mode>/${mode}/" apex_tracker_tmp.yml
sed -i -e "s/<audio>/${audio}/" apex_tracker_tmp.yml
sed -i -e "s/<debug>/${debug}/" apex_tracker_tmp.yml
sed -i -e "s/<delay>/false/" apex_tracker_tmp.yml
sed -i -e "s/<replica>/1/" apex_tracker_tmp.yml

echo "docker-compose yaml:"
cat apex_tracker_tmp.yml

echo "run docker:"

docker-compose -f apex_tracker_tmp.yml up

if [ "$mode" == "match_clip" ]|| [ "$mode" == "match_clip_foreach" ]; then
    echo "Check if merge file is created"
    result_num=$(find . -name "${dummy_date}_*_merge.mp4" | grep -c "mp4" || true)
    if [ ${result_num} -ne ${expected_result} ]; then
        echo "[ERROR] Num of merged file doesn't match. [$result_num != $expected_result]"
        exit 1
    fi
fi

if [ "$mode" == "kill_clip" ]; then
    echo "Check if kill_clip is created"
    result_num=$(find ./apex_kill_clip/local -name "*.mp4" | grep -c "mp4" || true)
    if [ ${result_num} -ne ${expected_result} ]; then
        echo "[ERROR] Num of merged file doesn't match. [$result_num != $expected_result]"
        exit 1
    fi


fi


echo "run finished"
