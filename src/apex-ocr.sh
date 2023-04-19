#!/bin/bash

MOVIE_DIR=/Volumes/usbshare2/GameRecs2021
OUT_DIR=/Volumes/usbshare1-2/GameRecs2020/apex
FINISH_FLG=flg_ocr_finished
csv_file=cut_time_battle.csv


for movie_file in `ls $MOVIE_DIR/20*.mkv`
do
    echo "Start OCR $movie_file : "
    dir=`basename $movie_file | awk -F. '{print $1}'`
    mkdir -p ${OUT_DIR}/${dir}
    if [ ! -f ${OUT_DIR}/${dir}/${FINISH_FLG} ]; then
        rm -rf ${OUT_DIR}/${dir}/match*/
        rm ${OUT_DIR}/${dir}/flg_*
        rm ${OUT_DIR}/${dir}/*flg*
        python3 ./ocr/apex-ocr.py -o ${OUT_DIR} ${movie_file}
        if [ -s ${OUT_DIR}/${dir}/${csv_file} ]; then
            touch ${OUT_DIR}/${dir}/${FINISH_FLG}
        fi
    else
        echo "Skip OCR ${OUT_DIR}/${dir}"
    fi
done
