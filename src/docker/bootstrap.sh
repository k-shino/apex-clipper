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
export DEBUG_MODE=${DEBUG_MODE:-false}
export SKIP_IMAGE_EXPORT=${SKIP_IMAGE_EXPORT:-false}

export IS_START_DELAY=${IS_START_DELAY:-true}

export REVERT=false

export MOVIE_DIR_LIST=$(ls $SRC_MOVIE_PATH | sort -R)

export AUDIO_CHANNEL=${AUDIO_CHANNEL:-0}

#############################
PROGNAME=$(basename "$0")
VERSION=${VERSION:-"3.13"}
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
        '--imageexport' )
            SKIP_IMAGE_EXPORT=true
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
    # set -x
    :
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
find "$SRC_MOVIE_PATH"
echo "  -----------"
echo -n "  OUT_PATH:"
echo "$OUT_PATH"
# ls -al "$OUT_PATH"
echo "  -----------"
echo -n "  OCR_PATH:"
echo "$OCR_PATH"
# ls -al "$OCR_PATH"
echo "  -----------"
echo -n "  WORK_PATH:"
echo "$WORK_PATH"
# ls -al "$WORK_PATH"
echo "  -----------"
if "$IS_START_DELAY"; then
    sec=$((RANDOM % 100))
    echo "Sleep $sec sec..."
    sleep $sec
else
    echo "Skip sleep[IS_START_DELAY = false]"
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
            list=$(find "$SRC_MOVIE_PATH/$MOVIE_DIR" -name "*.mp4" -o -name "*.mkv" | sort -r)
        else
            list=$(find "$SRC_MOVIE_PATH/$MOVIE_DIR" -name "*.mp4" -o -name "*.mkv" | sort -R)
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
            
            # ocrが終わっていない場合の処理
            if [ ! -f "${OCR_PATH}/${dir}/${FINISH_FLG}" ]; then
                # file_sizeに${movie_file}のファイルサイズを保存する。
                file_size=$(ls -al ${movie_file} | awk '{print $5}')

                # このファイルサイズが、次回以降のループ時に不一致になった場合、$flg_ocr_in_progressを削除する
                if [ -f "$flg_ocr_in_progress" ]; then
                    if [ "$(cat "$flg_ocr_in_progress")" != "$file_size" ]; then
                        echo "  apex-tracker: rm ${flg_ocr_in_progress} [may video files has'nt finalized yet] (file_size=${file_size}, flg_ocr_in_progress=$(cat "${flg_ocr_in_progress}"))"
                        rm -f "$flg_ocr_in_progress"
                    fi
                fi

                # flg_in_progressがある場合はskipする
                if [ ! -f "${flg_ocr_in_progress}" ]; then
                    # rm -rf ${OCR_PATH}/${dir}/match*/
                    rm -f "${OCR_PATH}/${dir}"/flg_*
                    rm -f "${OCR_PATH}/${dir}"/*flg*
                    ls -al ${movie_file} | awk '{print $5}' > "$flg_ocr_in_progress"

                    EXEC_OCR="python3 /root/apex-ocr.py -o \"${OCR_PATH}\""
                    EXEC_ARGS=""

                    if [ -n "$SKIP" ]; then
                        EXEC_ARGS="$EXEC_ARGS --skip $SKIP"
                    fi

                    if "$DEBUG_MODE"; then
                        EXEC_ARGS="$EXEC_ARGS --debug"
                    fi

                    if "$SKIP_IMAGE_EXPORT"; then
                        EXEC_ARGS="$EXEC_ARGS --skipimage"
                    fi

                    echo "    exec: $EXEC_OCR $EXEC_ARGS ${movie_file}"
                    if ! eval "$EXEC_OCR $EXEC_ARGS \"${movie_file}\"";
                    then
                        touch "${OCR_PATH}/${dir}"/file_error
                        rm -f "$flg_ocr_in_progress"
                        # exit 1
                    fi

                    if [ -s "${OCR_PATH}/${dir}/${csv_file}" ]; then
                        echo $VERSION > "${OCR_PATH}/${dir}/${FINISH_FLG}"
                        echo "    Finish OCR ${OCR_PATH}/${dir}"
                        rm -f "$flg_ocr_in_progress"

                        # ${OCR_PATH}/${dir}の中に、flg_in_progress_matchがある場合、削除し、ocr_finishedファイルを作成する
                        for match in $(find "${OCR_PATH}/${dir}" -maxdepth 1 -type d | grep match)
                        do
                            rm -f "${match}"/flg_in_progress_match
                            touch "${match}"/ocr_finished
                        done
                    fi
                else
                    echo "    Another OCR process running for ${OCR_PATH}/${dir} (work_in_progress flag)"
                fi
            # ocrが終わっていた場合はSkip
            else
                echo "    Skip OCR ${OCR_PATH}/${dir}"
            fi
        done < <(echo "$list")
    done
fi

# マッチクリップの作成
if [ "$MODE" == 'all' ] || [ "$MODE" == 'match_clip' ]; then
    echo "---------------------------------------------------"
    echo "Create match-clip phase"
    echo "---------------------------------------------------"
    list=$(find "$SRC_MOVIE_PATH/$MOVIE_DIR" -name "*.mp4" -o -name "*.mkv" | sort -r)
    if "$REVERT"; then
        list=$(echo "$list" | sort -r)
    else
        list=$(echo "$list" | sort -R)
    fi
    # for file in $list
    # do
    while read -r file
    do

        echo "-----------------------------------------"
        echo "apex-tracker: Start extract file $file"
        echo "-----------------------------------------"

        b_name=$(basename "$file")
        filename=${b_name%.*}
        mkdir -p "${WORK_PATH}/${filename}"
        export_dir=${WORK_PATH}/${filename}
        battle_dir=${export_dir}/${filename}_battle
        flg_finish=${export_dir}/${filename}_flg_extracted
        file_locked=${export_dir}/${filename}_flg_locked
        flg_in_progress=${export_dir}/${filename}_flg_in_progress
        flg_ocr_finished=${OCR_PATH}/${filename}/flg_ocr_finished
        check_csv_battle=${export_dir}/${csv_file}


        if [ -f "${flg_ocr_finished}" ]; then
            # if [ $FORCE_PARAM ]; then
            #     echo "apex-tracker: [FORCE] rm $check_csv_battle, $check_csv_battle"
            #     rm -f $check_csv_battle
            # fi

            # 元の動画ファイルのサイズを確認し、$file_lockedにサイズ値を格納する。
            # サイズ値が次回以降のループ時に不一致になった場合、$export_dirを初期化する
            file_size=$(ls -al /root/src_movie/*/"${filename}"* | awk '{print $5}')
            if [ -f "$file_locked" ]; then
                if [ "$(cat "$file_locked")" != "$file_size" ]; then
                    echo "  apex-tracker: rm ${export_dir} [may video files has'nt finalized yet] (file_size=${file_size}, file_locked=$(cat "${file_locked}"))"
                    rm -rf "${export_dir}"
                    mkdir -p "${export_dir}"
                fi
            fi
            echo -n "$file_size" > "$file_locked"

            if [ ! -f "$flg_finish" ] || "${FORCE_PARAM}"; then
                if [ ! -f "$flg_in_progress" ]; then
                    echo "  apex-tracker: Start normal extract process : $file is flagged as WIP."
                    touch "$flg_in_progress"
                    # if [ ! -f $check_csv_battle ]; then
                    #     python /root/apex-ocr.py $file -o $OUT_PATH 
                    # fi
                    for match in $(find "${export_dir}" -maxdepth 1 -type d | grep match)
                    do
                        rm -rf "${match}"/rec
                    done

                    EXEC_OCR="python /root/apex-create-movie.py \"$file\" --output \"$OUT_PATH\" --ocr \"$OCR_PATH\" --audio \"$AUDIO_CHANNEL\""
                    
                    unset $EXEC_ARGS

                    if "$DEBUG_MODE"; then
                        EXEC_ARGS="$EXEC_ARGS --debug"
                    fi

                    echo "    -----------------------------------------"
                    echo "    exec: $EXEC_OCR $EXEC_ARGS"
                    echo "    -----------------------------------------"

                    eval $EXEC_OCR $EXEC_ARGS

                    echo "    -----------------------------------------"
                    echo "    finished exec: $EXEC_OCR $EXEC_ARGS"
                    echo "    -----------------------------------------"

                    echo "    -----------------------------------------"
                    echo "    Show movie files:"
                    find / -type f -name '*.mp4'
                    # find "${WORK_PATH}/${filename}" -type f -name '*.mp4'
                    echo "    -----------------------------------------"


                    while read -r match
                    do
                    # for match in $(find "${export_dir}" -maxdepth 1 -type d | grep match)
                    # do
                        echo "      -----------------------------------------"
                        echo "      start merge clips match $match"
                        echo "      -----------------------------------------"
                        merge_file="${match}"/merge.txt
                        output_file="${OUT_PATH}/${filename}"_$(basename "$match")_merge.mp4

                        if "$FORCE_PARAM" ; then
                            echo "    apex-tracker: [FORCE] rm $merge_file, $output_file"
                            rm -f "$merge_file"
                            rm -f "$output_file"
                        fi

                        : > "$merge_file"

                        echo "    apex-tracker: create merge_file: ${merge_file}"
                        for in_file_number in $(find "${match}"/rec -type f -name '*battle*.mp4' | sed -e 's/.*battle//g' | sed -e 's/_.*//g' | sort -n)
                        do
                            in_file=$(find "${match}"/rec -type f -name "*battle${in_file_number}*")
                            # in_file=$(ls "${match}/rec/*battle${in_file_number}*".mp4)
                            echo "file '$in_file'" >> "$merge_file"
                        done

                        echo "      Show ${merge_file} :"
                        echo "      ----------------------------------------------"
                        cat "$merge_file"
                        echo "      ----------------------------------------------"

                        echo "    apex-tracker: start merge clipped files : ${merge_file}"
                        ffmpeg -y -f concat -safe 0 -i "$merge_file" -c copy "$output_file" </dev/null
                        # ffmpeg -y -f concat -safe 0 -i $merge_file -c copy -map 0:0 -map 0:1 -map 0:2 -map 0:3 $output_file </dev/null > /dev/null 2>&1
                        echo "      ffmpeg -y -f concat -safe 0 -i \"$merge_file\" -c copy $output_file"
                        echo "      -----------------------------------------"
                        echo "      finish merge clips match $match"
                        echo "      -----------------------------------------"

                        if ! "$DEBUG_MODE"; then
                            rm -rf "${match}/rec"
                        fi

                    # done
                    done < <(find "${export_dir}" -maxdepth 1 -type d | grep match)
                    # for match in `find ${export_dir} -maxdepth 1 -type d | grep match`
                    # do
                    #     rm -rf ${match}/rec
                    # done

                    echo $VERSION > "$flg_finish"
                    rm -f "$flg_in_progress"
                else
                    echo "  apex-tracker: Skip $file [WIP]"
                fi
            else
                echo "  apex-tracker: Skip $file [Already finished]"
            fi
        else
            echo "    OCR process still running for ${export_dir} (work_in_progress flag)"
        fi

    done < <(echo "$list")

    # done
fi


# マッチクリップの作成
if [ "$MODE" == 'match_clip_foreach' ]; then
    echo "---------------------------------------------------"
    echo "Create match-clip phase(foreach option)"
    echo "---------------------------------------------------"
    list=$(find "$SRC_MOVIE_PATH/$MOVIE_DIR" -name "*.mp4" -o -name "*.mkv" | sort -R)
    if "$REVERT"; then
        list=$(echo "$list" | sort -r)
    else
        list=$(echo "$list" | sort -R)
    fi
    # for file in $list
    # do
    while read -r file
    do

        echo "-----------------------------------------"
        echo "apex-tracker: Start extract file $file"
        echo "-----------------------------------------"

        b_name=$(basename "$file")
        filename=${b_name%.*}
        mkdir -p "${WORK_PATH}/${filename}"
        export_dir=${WORK_PATH}/${filename}
        battle_dir=${export_dir}/${filename}_battle
        flg_finish=${export_dir}/${filename}_flg_extracted
        file_locked=${export_dir}/${filename}_flg_locked
        flg_in_progress=${export_dir}/${filename}_flg_in_progress
        flg_ocr_finished=${OCR_PATH}/${filename}/flg_ocr_finished
        check_csv_battle=${export_dir}/${csv_file}

        # 元の動画ファイルのサイズを確認し、$file_lockedにサイズ値を格納する。
        # サイズ値が次回以降のループ時に不一致になった場合、$export_dirを初期化する
        # file_size=$(ls -al /root/src_movie/*/"${filename}"* | awk '{print $5}')
        # if [ -f "$file_locked" ]; then
        #     if [ "$(cat "$file_locked")" != "$file_size" ]; then
        #         echo "  apex-tracker: rm ${export_dir} [may video files has'nt finalized yet] (file_size=${file_size}, file_locked=$(cat "${file_locked}"))"
        #         rm -rf "${export_dir}"
        #         mkdir -p "${export_dir}"
        #     fi
        # fi
        # echo -n "$file_size" > "$file_locked"

        # if [ ! -f $check_csv_battle ]; then
        #     python /root/apex-ocr.py $file -o $OUT_PATH 
        # fi
        # for match in $(find "${export_dir}" -maxdepth 1 -type d | grep match)
        # do
        #     rm -rf "${match}"/rec
        # done

        for match in $(find "${OCR_PATH}/${filename}" -maxdepth 1 -type d | grep match | sort -R)
        do
            match_in_progress=${match}/flg_create_clip_in_progress
            match_finished=${match}/flg_create_clip_finished
            

            MATCH_NUM=$(echo ${match} | sed -e 's/.*match//')
            # ${OCR_PATH}/${filename}/$MATCH_NUMの中に、ocr_finishedがある場合、以下を実行する
            if [ -f "${match}"/ocr_finished ]; then
                # match_in_progressまたはmatch_finishedがある場合はskipする
                if [ ! -f "${match_in_progress}" ] && [ ! -f "${match_finished}" ]; then
                    echo "  apex-tracker: Start normal extract process : $file is flagged as WIP."
                    touch "$match_in_progress"

                    EXEC_OCR="python /root/apex-create-movie-each.py \"$file\" --output \"$OUT_PATH\" --ocr \"$OCR_PATH\" --audio \"$AUDIO_CHANNEL\" --match ${MATCH_NUM}"
                    
                    unset $EXEC_ARGS

                    if "$DEBUG_MODE"; then
                        EXEC_ARGS="$EXEC_ARGS --debug"
                    fi

                    echo "    -----------------------------------------"
                    echo "    exec: $EXEC_OCR $EXEC_ARGS"
                    echo "    -----------------------------------------"

                    eval $EXEC_OCR $EXEC_ARGS

                    echo "    -----------------------------------------"
                    echo "    finished exec: $EXEC_OCR $EXEC_ARGS"
                    echo "    -----------------------------------------"

                    echo "    -----------------------------------------"
                    echo "    Show movie files:"
                    find / -type f -name '*.mp4'
                    # find "${WORK_PATH}/${filename}" -type f -name '*.mp4'
                    echo "    -----------------------------------------"


                    while read -r match
                    do
                    # for match in $(find "${export_dir}" -maxdepth 1 -type d | grep match)
                    # do
                        
                        count_movie_file=$(find /root/work -name "*.mp4" | grep -c .mp4 || true)
                        if [ $count_movie_file -eq 0 ]; then
                            echo "No movie file is exported. merge process is skipped."
                            exit 0
                        fi
                        
                        echo "      -----------------------------------------"
                        echo "      start merge clips match $match"
                        echo "      -----------------------------------------"
                        merge_file="${match}"/merge.txt
                        output_file="${OUT_PATH}/${filename}"_$(basename "$match")_merge.mp4

                        if "$FORCE_PARAM" ; then
                            echo "    apex-tracker: [FORCE] rm $merge_file, $output_file"
                            rm -f "$merge_file"
                            rm -f "$output_file"
                        fi

                        : > "$merge_file"

                        echo "    apex-tracker: create merge_file: ${merge_file}"
                        for in_file_number in $(find "${match}"/rec -type f -name '*battle*.mp4' | sed -e 's/.*battle//g' | sed -e 's/_.*//g' | sort -n)
                        do
                            in_file=$(find "${match}"/rec -type f -name "*battle${in_file_number}*")
                            # in_file=$(ls "${match}/rec/*battle${in_file_number}*".mp4)
                            echo "file '$in_file'" >> "$merge_file"
                        done

                        echo "      Show ${merge_file} :"
                        echo "      ----------------------------------------------"
                        cat "$merge_file"
                        echo "      ----------------------------------------------"

                        echo "    apex-tracker: start merge clipped files : ${merge_file}"
                        ffmpeg -y -f concat -safe 0 -i "$merge_file" -c copy "$output_file" </dev/null
                        # ffmpeg -y -f concat -safe 0 -i $merge_file -c copy -map 0:0 -map 0:1 -map 0:2 -map 0:3 $output_file </dev/null > /dev/null 2>&1
                        echo "      ffmpeg -y -f concat -safe 0 -i \"$merge_file\" -c copy $output_file"
                        echo "      -----------------------------------------"
                        echo "      finish merge clips match $match"
                        echo "      -----------------------------------------"
                    # done
                    done < <(find "${export_dir}" -maxdepth 1 -type d | grep match)
                    rm -rf "${match}"/rec
                    # for match in `find ${export_dir} -maxdepth 1 -type d | grep match`
                    # do
                    #     rm -rf ${match}/rec
                    # done


                    echo $VERSION > "$match_finished"
                    rm -f "$match_in_progress"
                fi
            else
                echo "${match} is skipped."
            fi
        done


    done < <(echo "$list")

    # done
fi


# リザルトをファイル名に付与
if [ $MODE == 'all' ] || [ $MODE == 'add_result' ]; then
    echo "---------------------------------------------------"
    echo "Add battle result phase"
    echo "---------------------------------------------------"
    echo "/root/apex-ocr-exporter.sh -b ${OUT_PATH} -o ${OCR_PATH} -d ${OUT_PATH} --mode result"
    cat /root/apex-ocr-exporter.sh
    /root/apex-ocr-exporter.sh -b ${OUT_PATH} -o ${OCR_PATH} -d ${OUT_PATH} -w ${WORK_PATH} --mode result
fi

# キルクリップ
if [ $MODE == 'all' ] || [ $MODE == 'kill_clip' ]; then
    echo "---------------------------------------------------"
    echo "Create kill clip phase"
    echo "---------------------------------------------------"
    mkdir -p ${KILL_CLIP_PATH}

    type_list=${type_list:-"default"}

    EXEC_KILL_CLIP="/root/apex-kill-clip.sh --out ${KILL_CLIP_PATH} --movie ${SRC_MOVIE_PATH} --ocr ${OCR_PATH} --type ${type_list} -a ${AUDIO_CHANNEL}"

    if "$REVERT"; then
        EXEC_KILL_CLIP_ARGS=" --revert"
    fi

    echo "$EXEC_KILL_CLIP $EXEC_KILL_CLIP_ARGS"
    eval "$EXEC_KILL_CLIP $EXEC_KILL_CLIP_ARGS"

fi
