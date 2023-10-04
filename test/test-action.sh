#!/bin/bash

set -eux

tmpdir=${tmpdir:-tmp}
target=${target:-clip}
mode=${mode:-ocr}
audio=${audio:-1}
expected_result=${expected_result:-1}
debug=${debug:-false}
clean=${clean:-true}
dryrun=${dryrun:-false}
ocr_in_progress=${ocr_in_progress:-false}
skipimage=${skipimage:-false}
match_num=${match_num:-}

dummy_date="2023-08-01_10-00-00"

# cd ../src

# docker build -f ./docker/Dockerfile-arm64 -t apex-clipper:local .

cd ../test

if "$clean"; then
    rm -rf ${tmpdir}
fi
mkdir -p ${tmpdir}
cd ${tmpdir}
mkdir -p orig out ocr work apex_kill_clip
if "$clean"; then
    cp "../orig/${target}.mp4" orig/${dummy_date}.mp4
fi

if [ "$mode" == "match_clip" ]|| [ "$mode" == "match_clip_foreach" ] || [ "$mode" == "kill_clip" ]; then
    if "$clean"; then
        cp -r "../ocr/${target}" ./ocr/${dummy_date}
    fi

    if [ -n "${match_num}" ]; then
        rm -f ./ocr/${dummy_date}/match${match_num}/flg_create_clip_finished
    fi

    if "$ocr_in_progress"; then
        for dir in match1 match2
        do
            if [ -d ./ocr/${dummy_date}/${dir} ]; then
                rm ./ocr/${dummy_date}/${dir}/ocr_finished
                touch ./ocr/${dummy_date}/${dir}/flg_in_progress_match
            fi
        done
    fi
fi

cp ../apex_tracker.yml apex_tracker_tmp.yml

sed -i -e "s/<image-tag>/apex-clipper:local/" apex_tracker_tmp.yml
sed -i -e "s/<mode>/${mode}/" apex_tracker_tmp.yml
sed -i -e "s/<audio>/${audio}/" apex_tracker_tmp.yml
sed -i -e "s/<debug>/${debug}/" apex_tracker_tmp.yml
sed -i -e "s/<dryrun>/${dryrun}/" apex_tracker_tmp.yml
sed -i -e "s/<delay>/false/" apex_tracker_tmp.yml
sed -i -e "s/<replica>/1/" apex_tracker_tmp.yml
sed -i -e "s/<skipimage>/${skipimage}/" apex_tracker_tmp.yml


echo "docker-compose yaml:"
cat apex_tracker_tmp.yml

echo "run docker:"

docker-compose -f apex_tracker_tmp.yml up

if [ "$mode" == "ocr" ]; then

    echo "Check if kill scene is counted"
    result_num=$(cat ocr/${dummy_date}/cut_time_battle.csv | grep -c ,8, || true)
    if [ ${result_num} -ne ${expected_result} ]; then
        echo "[ERROR] Num of kill scene doesn't match. [$result_num != $expected_result]"
        exit 1
    fi
fi

if [ "$mode" == "match_clip" ]; then
    echo "Check if merge file is created"
    result_num=$(find . -name "${dummy_date}_*_merge.mp4" | grep -c "mp4" || true)
    if [ ${result_num} -ne ${expected_result} ]; then
        echo "[ERROR] Num of merged file doesn't match. [$result_num != $expected_result]"
        exit 1
    fi
fi

if [ "$mode" == "match_clip_foreach" ]; then
    if "$ocr_in_progress"; then
        echo "Check file"
        result_num=$(find . -name "*_flg_locked" | grep -c flg_locked || true)
        if [ $result_num -ne 0 ]; then
            echo "[ERROR] flg_locked file exists"
            find . -name "*_flg_locked"
            exit 1
        fi
    else
        echo "Check if merge file is created"
        result_num=$(find . -name "${dummy_date}_*_merge.mp4" | grep -c "mp4" || true)
        if [ ${result_num} -ne ${expected_result} ]; then
            echo "[ERROR] Num of merged file doesn't match. [$result_num != $expected_result]"
            exit 1
        fi
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
