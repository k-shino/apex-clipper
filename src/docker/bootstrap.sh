#!/bin/bash

# set -x

export out=/root/out
export SRC_MOVIE_PATH=${SRC_MOVIE_PATH:-/root/src_movie}
export OUT_PATH=${OUT_PATH:-/root/out}
export OCR_PATH=${OCR_PATH:-/root/ocr}
export WORK_PATH=${WORK_PATH:-/root/work}
export KILL_CLIP_PATH=${KILL_CLIP_PATH:-/root/apex_kill_clip}

export FINISH_FLG=${FINISH_FLG:-flg_ocr_finished}
export csv_file=${csv_file:-cut_time_battle.csv}

export MODE=${MODE:-all}
export FORCE_PARAM=false
export DEBUG_MODE=false

export REVERT=false

export MOVIE_DIR_LIST=$(ls $SRC_MOVIE_PATH | sort -R)

#############################
PROGNAME=$(basename "$0")
VERSION="3.11"
#############################

usage() {
#    echo "Kubernetes Master deployment script for ubuntu."
#    echo "Usage: $PROGNAME [OPTIONS] IPADDR"
    echo ""
    echo "Options:"
    echo "  -h, --help"
    echo "      --version"
    exit 1
}

for OPT in "$@"
do
    case "$OPT" in
        '-h'|'--help' )
            usage
            ;;
        '--version' )
            echo $VERSION
            exit 1
            ;;
        '-f'|'--force' )
            FORCE_PARAM=true
            shift 1
            ;;
        '-m'|'--mode' )
            MODE=$2
            shift 1
            ;;
        '--debug' )
            DEBUG_MODE=true
            shift 1
            ;;
        '--revert' )
            REVERT=true
            shift 1
            ;;
        '-t'|'--type' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            type_list=$2
            shift 2
            ;;
        '--skip' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            SKIP=$2
            shift 2
            ;;
        '-a'|'--audio' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            AUDIO_CHANNEL="$2"
            shift 2
            ;;
        '--'|'-' )
            shift 1
            param+=( "$@" )
            break
            ;;
        -*)
            echo "$PROGNAME: illegal option -- '$(echo $1 | sed 's/^-*//')'" 1>&2
            exit 1
            ;;
        *)
            if [[ ! -z "$1" ]] && [[ ! "$1" =~ ^-+ ]]; then
                #param=( ${param[@]} "$1" )
                param+=( "$1" )
                shift 1
            fi
            ;;
    esac
done

if "$DEBUG_MODE"; then
    set -x
fi

echo "---------------------------------------------------"
echo "apex_tracker version $VERSION"
echo "---------------------------------------------------"
echo "Envirionment:"
echo "  MODE: $MODE"
echo " "
echo "Check files:"
echo -n "  SRC_MOVIE:"
ls -C "$SRC_MOVIE_PATH"
echo "  -----------"
echo -n "  OUT_PATH:"
echo "$OUT_PATH"
ls -al "$OUT_PATH"
echo "  -----------"
echo -n "  OCR_PATH:"
echo "$OCR_PATH"
ls -al "$OCR_PATH"
echo "  -----------"
echo -n "  WORK_PATH:"
echo "$WORK_PATH"
ls -al "$WORK_PATH"
echo "  -----------"
if ! "$DEBUG_MODE"; then
    sec=$((RANDOM % 100))
    echo "Sleep $sec sec..."
    sleep $sec
else
    sec=$((RANDOM % 10))
    echo "Sleep $sec sec..."
    sleep $sec
fi

# OCRの実行
if [ "$MODE" == 'all' ] || [ "$MODE" == 'ocr' ]; then
    echo "---------------------------------------------------"
    echo "OCR phase"
    echo "---------------------------------------------------"
    for MOVIE_DIR in ${MOVIE_DIR_LIST}
    do
        echo "MOVIE_DIR: $SRC_MOVIE_PATH/$MOVIE_DIR:"
        ls "$SRC_MOVIE_PATH/$MOVIE_DIR"
        if "$REVERT"; then
            list=$(find "$SRC_MOVIE_PATH/$MOVIE_DIR" -name '*.mp4' -o '*.mkv' | sort -r)
        else
            list=$(find "$SRC_MOVIE_PATH/$MOVIE_DIR" -name '*.mp4' -o '*.mkv' | sort -R)
        fi
        echo "list:"
        echo "$list"
        while read -r movie_file
        do
            echo "  Start OCR $movie_file : "
            dir=$(basename "$movie_file" | awk -F. '{print $1}')
            mkdir -p "${OCR_PATH}/${dir}"
            flg_ocr_in_progress=${OCR_PATH}/${dir}/flg_in_progress

            if "$FORCE_PARAM"; then
                if [ -f "${OCR_PATH}/${dir}/${FINISH_FLG}" ]; then
                    if [ "$(cat "${OCR_PATH}/${dir}/${FINISH_FLG}")" != "$VERSION" ]; then
                        echo "Force OCR: ${OCR_PATH}/${dir}"
                        rm -f "${OCR_PATH}/${dir}/${FINISH_FLG}"
                    fi
                fi
            fi

            if [ ! -f "${OCR_PATH}/${dir}/${FINISH_FLG}" ]; then
                if [ ! -f "${flg_ocr_in_progress}" ]; then
                    # rm -rf ${OCR_PATH}/${dir}/match*/
                    rm -f "${OCR_PATH}/${dir}"/flg_*
                    rm -f "${OCR_PATH}/${dir}"/*flg*
                    touch "$flg_ocr_in_progress"

                    EXEC_OCR="python3 /root/apex-ocr.py -o \"${OCR_PATH}\""
                    unset $EXEC_ARGS

                    if [ -n "$SKIP" ]; then
                        EXEC_ARGS="$EXEC_ARGS --skip $SKIP"
                    fi

                    if "$DEBUG_MODE"; then
                        EXEC_ARGS="$EXEC_ARGS --debug"
                    fi

                    echo "    exec: $EXEC_OCR $EXEC_ARGS ${movie_file}"
                    eval "$EXEC_OCR $EXEC_ARGS \"${movie_file}\""

                    if [ -s "${OCR_PATH}/${dir}/${csv_file}" ]; then
                        echo $VERSION > "${OCR_PATH}/${dir}/${FINISH_FLG}"
                        echo "    Finish OCR ${OCR_PATH}/${dir}"
                        rm -f "$flg_ocr_in_progress"
                    fi
                else
                    echo "    Another OCR process running for ${OCR_PATH}/${dir} (work_in_progress flag)"
                fi
            else
                echo "    Skip OCR ${OCR_PATH}/${dir}"
            fi
        done < <(echo "$list")
    done
fi

# マッチクリップの作成
if [ $MODE == 'all' -o $MODE == 'match_clip' ]; then
    echo "---------------------------------------------------"
    echo "Create match-clip phase"
    echo "---------------------------------------------------"
    list=`ls /root/src_movie/*/*.m* | sort -r | sed -e "s/\ /\\\\ /"`
    if "$REVERT"; then
        list=`echo $list | sort -r`
    else
        list=`echo $list | sort -R`
    fi
    for file in $list
    do
        echo "-----------------------------------------"
        echo "apex-tracker: Start extract file $file"
        echo "-----------------------------------------"

        b_name=`basename $file`
        filename=${b_name%.*}
        mkdir -p ${WORK_PATH}/${filename}
        export_dir=${WORK_PATH}/${filename}
        battle_dir=${export_dir}/${filename}_battle
        flg_finish=${export_dir}/${filename}_flg_extracted
        file_locked=${export_dir}/${filename}_flg_locked
        flg_in_progress=${export_dir}/${filename}_flg_in_progress
        check_csv_battle=${export_dir}/${csv_file}

        # if [ $FORCE_PARAM ]; then
        #     echo "apex-tracker: [FORCE] rm $check_csv_battle, $check_csv_battle"
        #     rm -f $check_csv_battle
        # fi

        file_size=`ls -al /root/src_movie/*/${filename}* | awk '{print $5}'`
        if [ -f $file_locked ]; then
            if [ "`cat $file_locked`" != "$file_size" ]; then
                echo "  apex-tracker: rm ${export_dir} [may video files has'nt finalized yet]"
                rm -rf ${export_dir}
                mkdir -p ${export_dir}
            fi
        fi
        echo -n $file_size > $file_locked

        if [ ! -f $flg_finish ] || "${FORCE_PARAM}"; then
            if [ ! -f $flg_in_progress ]; then
                echo "  apex-tracker: Start normal extract process : $file is flagged as WIP."
                touch $flg_in_progress
                # if [ ! -f $check_csv_battle ]; then
                #     python /root/apex-ocr.py $file -o $OUT_PATH 
                # fi
                for match in `find ${export_dir} -maxdepth 1 -type d | grep match`
                do
                    rm -rf ${match}/rec
                done

                EXEC_OCR='python /root/apex-create-movie.py $file --output $OUT_PATH --ocr $OCR_PATH'
                
                unset $EXEC_ARGS
                if [ -n "$AUDIO_CHANNEL" ]; then
                     EXEC_ARGS="$EXEC_ARGS --audio $AUDIO_CHANNEL"
                fi

                echo "    -----------------------------------------"
                echo "    exec: $EXEC_OCR $EXEC_ARGS"
                echo "    -----------------------------------------"

                eval $EXEC_OCR $EXEC_ARGS

                echo "    -----------------------------------------"
                echo "    finished exec: $EXEC_OCR $EXEC_ARGS"
                echo "    -----------------------------------------"

                for match in `find ${export_dir} -maxdepth 1 -type d | grep match`
                do
                    echo "      -----------------------------------------"
                    echo "      start merge clips match $match"
                    echo "      -----------------------------------------"
                    merge_file=${match}/Apex_Legends_digest_${filename}_merge.txt
                    output_file=${OUT_PATH}/${filename}_`basename $match`_merge.mp4

                    if "$FORCE_PARAM" ; then
                        echo "    apex-tracker: [FORCE] rm $merge_file, $output_file"
                        rm -f $merge_file
                        rm -f $output_file
                    fi

                    : > $merge_file

                    echo "    apex-tracker: create merge_file: ${merge_file}"
                    for in_file_number in `ls ${match}/rec/${filename}*.mp4 | sed -e 's/.*battle//g' | sed -e 's/_.*//g' | sort -n`
                    do
                        in_file=`ls ${match}/rec/*battle${in_file_number}*.mp4`
                        echo "file $in_file" >> $merge_file
                    done

                    echo "      Show ${merge_file} :"
                    echo "      ----------------------------------------------"
                    cat $merge_file
                    echo "      ----------------------------------------------"

                    echo "    apex-tracker: start merge clipped files : ${merge_file}"
                    ffmpeg -y -f concat -safe 0 -i $merge_file -c copy -map 0:0 -map 0:1 -map 0:2 -map 0:3 $output_file </dev/null
                    # ffmpeg -y -f concat -safe 0 -i $merge_file -c copy -map 0:0 -map 0:1 -map 0:2 -map 0:3 $output_file </dev/null > /dev/null 2>&1
                    echo "      ffmpeg -y -f concat -safe 0 -i $merge_file -c copy -map 0:0 -map 0:1 -map 0:2 -map 0:3 $output_file"
                    echo "      -----------------------------------------"
                    echo "      finish merge clips match $match"
                    echo "      -----------------------------------------"
                done
                # for match in `find ${export_dir} -maxdepth 1 -type d | grep match`
                # do
                #     rm -rf ${match}/rec
                # done

                echo $VERSION > $flg_finish
                rm -f $flg_in_progress
            else
                echo "  apex-tracker: Skip $file [WIP]"
            fi
        else
            echo "  apex-tracker: Skip $file [Already finished]"
        fi

    done
fi

# リザルトをファイル名に付与
if [ $MODE == 'all' -o $MODE == 'add_result' ]; then
    echo "---------------------------------------------------"
    echo "Add battle result phase"
    echo "---------------------------------------------------"
    echo "/root/apex-ocr-exporter.sh -b ${OUT_PATH} -o ${OCR_PATH} -d ${OUT_PATH} --mode result"
    cat /root/apex-ocr-exporter.sh
    /root/apex-ocr-exporter.sh -b ${OUT_PATH} -o ${OCR_PATH} -d ${OUT_PATH} -w ${WORK_PATH} --mode result
fi

# キルクリップ
if [ $MODE == 'all' -o $MODE == 'kill_clip' ]; then
    echo "---------------------------------------------------"
    echo "Create kill clip phase"
    echo "---------------------------------------------------"
    mkdir -p ${KILL_CLIP_PATH}

    type_list=${type_list:-"default"}

    if "$REVERT"; then
        echo "/root/apex-kill-clip.sh --out ${KILL_CLIP_PATH} --movie ${SRC_MOVIE_PATH} --ocr ${OCR_PATH} --revert --type ${type_list}"
        /root/apex-kill-clip.sh --out ${KILL_CLIP_PATH} --movie ${SRC_MOVIE_PATH} --ocr ${OCR_PATH} --revert --type ${type_list}
    else
        echo "/root/apex-kill-clip.sh --out ${KILL_CLIP_PATH} --movie ${SRC_MOVIE_PATH} --ocr ${OCR_PATH} --type ${type_list}"
        /root/apex-kill-clip.sh --out ${KILL_CLIP_PATH} --movie ${SRC_MOVIE_PATH} --ocr ${OCR_PATH} --type ${type_list}
    fi

    # echo "/root/apex-ocr-exporter.sh -b ${OUT_PATH} -o ${OCR_PATH} -d ${OUT_PATH} --mode result"
    # /root/apex-ocr-exporter.sh -b ${OUT_PATH} -o ${OCR_PATH} -d ${OUT_PATH} -w ${WORK_PATH} --mode result
fi
