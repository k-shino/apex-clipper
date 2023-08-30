#!/bin/bash

set -e

#############################
PROGNAME=$(basename $0)
VERSION="0.21"
DRY_RUN=false
REVERT=false
type_list="champion blackhole kill knock kd death"

#############################

usage() {
#    echo "Kubernetes Master deployment script for ubuntu."
#    echo "Usage: $PROGNAME [OPTIONS] IPADDR"
    echo ""
    echo "Options:"
    echo "  -m, --movie"
    echo "      Input movie file"
    echo "  -o, --ocr"
    echo "      Input ocr directory"
    echo "  -d, --dir"
    echo "      --csv export directory"
    echo "  -h, --help"
    echo "      --version"
    exit 1
}

for OPT in "$@"
do
    case "$OPT" in
        '-h'|'--help' )
            usage
            exit 1
            ;;
        '--version' )
            echo $VERSION
            exit 1
            ;;
        '-m'|'--movie' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            movie_directories=$2
            shift 2
            ;;
        '-o'|'--ocr' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            ocr_whole_dir=$2
            shift 2
            ;;
        '-d'|'--dir' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            out_dir=$2
            shift 2
            ;;
        '-a'|'--audio' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            audio=$2
            shift 2
            ;;
        '-t'|'--type' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            type_list=$2
            shift 2
            ;;
        '--out' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            out_dir=$2
            shift 2
            ;;
        '--mode' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            mode=$2
            shift 2
            ;;
        '--dry-run' )
            DRY_RUN=true
            shift 1
            ;;
        '--revert' )
            REVERT=true
            shift 1
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

if [ -z "$movie_directories" ]; then
    echo "Movie parameter is empty"
    exit 1
fi

if [ -z "$ocr_whole_dir" ]; then
    echo "Ocr parameter is empty"
    exit 1
fi

if [ "$type_list" = "default" ]; then
    type_list="champion blackhole kill knock kd death"
fi

out_dir=${out_dir:="/Volumes/SSD-PGU3/GameRecs/apex"}
# apex_tracker_dir=${apex_tracker_dir:=/Users/nock/Documents/Codes/apex-tracker}

ocr_whole_dir=$(echo "$ocr_whole_dir" | sed -e 's/\/$//g')

audio=${audio:-0}

echo OCR directory: "$ocr_whole_dir"

# flg='flg_kill_clipped'
log='kill_clipped_'$(hostname)'.log'

movie_duration=30
battle_duration=90
champion_duration=180
blackhole_duration=60
death_duration=120
#echo "MODE: $mode"

################################
# csvファイル準備
################################
export_csv_dir=$out_dir
export_csv_local_dir=$export_csv_dir/local
export_csv_work_dir=$out_dir/.work
mkdir -p "$export_csv_dir"
rm -rf "$export_csv_work_dir"
mkdir -p "$export_csv_work_dir"
mkdir -p "$export_csv_local_dir"
export_csv_file=${export_csv_work_dir}/kill_clip.csv
export_csv_file_work=${export_csv_work_dir}/kill_clip_work.csv
export_csv_file_ocr_work=${export_csv_work_dir}/kill_clip_work_ocr.csv
export_csv_file_cam_work=${export_csv_work_dir}/kill_clip_work_cam.csv
ffmpeg_command=${export_csv_work_dir}/ffmpeg_command.sh
rm -f "$export_csv_file_work" "$export_csv_file_ocr_work" "${ffmpeg_command}"
touch "$export_csv_file_ocr_work" "$export_csv_file_cam_work" "$export_csv_file" "${ffmpeg_command}"

echo "----------------------------------------------"
echo "Create kill clip"
echo "Create kill clip" >> "${export_csv_dir}/${log}"
echo "  type_list: $type_list"

for movie_directory in $(echo "$movie_directories" | sed -e 's/,/ /g')
do
    echo Movie directory: "$movie_directory"
    movie_directory=$(echo "$movie_directory" | sed -e 's/\/$//g')

    for ocr_dir in $ocr_whole_dir
    do
        echo " ocr_dir: ${ocr_dir}"
        for type in $type_list
        do
            echo "  type: $type:"
            for movie_file in $(find "$movie_directory" -name '*.m*')
            do
                movie_date=$(echo "$movie_file" | xargs basename | awk -F[.] '{print $1}' | sed -e 's/-//g' | sed -e 's/://g' | sed -e 's/_//g' )
                # マッチしたOCRディレクトリと動画ファイルの処理
                # OCRディレクトリ : $ocr_dir
                # 動画ファイル : $movie_file
                echo "    movie_file: $movie_file"
                echo "    movie_file: $movie_file" >> "${export_csv_dir}/${log}"
                echo "    movie_date: $movie_date"
                echo "    movie_date: $movie_date" >> "${export_csv_dir}/${log}"
                movie_export_dirname=$(basename "$movie_file" | awk -F[.] '{print $1}')
                if [ -d "${ocr_dir}/${movie_export_dirname}" ]; then
                    echo "      directory ${ocr_dir}/${movie_export_dirname} exists:"

                    if [ -f "${ocr_dir}/${movie_export_dirname}/cut_time_battle.csv" ]; then

                        while IFS=',' read -ra fields; do
                            
                            # kill , championを抽出する（暫定）
                            if [ "${fields[1]}" -eq 8 ] || [ "${fields[1]}" -eq 9 ]; then

                                ################################
                                # 動画ファイルのUNIX TIMEを出力
                                ################################
                                movie_start_time=$(basename "$movie_file" | awk -F[-_.] '{print $1$2$3$4$5$6}')
                                #echo start time: $movie_start_time
                                movie_start_time_unix=$(echo "$movie_start_time" |
                                awk '{
                                # 年月日時分秒を取得
                                Y = substr($1, 1,4)*1;
                                M = substr($1, 5,2)*1; 
                                D = substr($1, 7,2)*1;
                                h = substr($1, 9,2)*1;
                                m = substr($1,11,2)*1;
                                s = substr($1,13  )*1;
                                # 計算公式に流し込む
                                if (M<3) {M+=12; Y--;} # 公式を使うための値調整
                                print (365*Y+int(Y/4)-int(Y/100)+int(Y/400)+int(306*(M+1)/10)-428+D-719163)*86400+(h*3600)+(m*60)+s;
                                }')
                                #echo $movie_start_time_unix
                                ################################
                                # 特徴点の動画ファイルでの秒数を算出
                                ################################
                                export_time_sec=${fields[0]}


                                this_export_time_unix=$(echo "scale=0; $movie_start_time_unix + $export_time_sec" | bc | sed 's/^\./0./' | sed -e 's/\..*//g')
                                ################################
                                # csvファイルを出力
                                ################################
                                echo "$this_export_time_unix $export_time_sec $movie_file $type ocr" >> "$export_csv_file_ocr_work"
                                echo "          Record: $export_time_sec,$movie_file ($this_export_time_unix - $movie_start_time_unix)" >> "${export_csv_dir}/${log}"
                                echo "          Record: $export_time_sec,$movie_file ($this_export_time_unix - $movie_start_time_unix)"


                            fi

                            # # fields配列には、行の各フィールドが格納される
                            # for field in "${fields[@]}"; do
                            #     echo "$field"
                            # done
                        done < "${ocr_dir}/${movie_export_dirname}/cut_time_battle.csv"

                    else
                        echo "No csv file found."
                    fi

                    # if [ $(find "${ocr_dir}/${movie_export_dirname}" -type d -name 'debug' -prune -o -name "*.jpg" | grep -v debug | grep -c ".jpg") -ne 0 ]; then
                    #     echo "      OCR picture exists in ${ocr_dir}/${movie_export_dirname}"
                    #     echo "      OCR picture exists in ${ocr_dir}/${movie_export_dirname}" >> "${export_csv_dir}/${log}"
                    #     # echo "debug ${ocr_dir}/$movie_export_dirname" 
                    #     # find ${ocr_dir}/$movie_export_dirname -name "${type}_*.jpg" || true
                    #     kill_clip_list=$(find "${ocr_dir}/$movie_export_dirname" -type d -name 'debug' -prune -o -name "${type}_*.jpg" | grep -v debug) || true
                    #     if [ -n "$kill_clip_list" ]; then
                    #     echo "        TYPE ${type} picture exists in ${ocr_dir}/${movie_export_dirname}"
                    #     echo "        TYPE ${type} picture exists in ${ocr_dir}/${movie_export_dirname}" >> "${export_csv_dir}/${log}"
                    #     fi
                    #     # echo "        kill_clip_list $kill_clip_list"
                    #     for kill_clip_file in $kill_clip_list
                    #     do
                    #         ################################
                    #         # 動画ファイルのUNIX TIMEを出力
                    #         ################################
                    #         movie_start_time=$(basename "$movie_file" | awk -F[-_.] '{print $1$2$3$4$5$6}')
                    #         #echo start time: $movie_start_time
                    #         movie_start_time_unix=$(echo "$movie_start_time" |
                    #         awk '{
                    #         # 年月日時分秒を取得
                    #         Y = substr($1, 1,4)*1;
                    #         M = substr($1, 5,2)*1; 
                    #         D = substr($1, 7,2)*1;
                    #         h = substr($1, 9,2)*1;
                    #         m = substr($1,11,2)*1;
                    #         s = substr($1,13  )*1;
                    #         # 計算公式に流し込む
                    #         if (M<3) {M+=12; Y--;} # 公式を使うための値調整
                    #         print (365*Y+int(Y/4)-int(Y/100)+int(Y/400)+int(306*(M+1)/10)-428+D-719163)*86400+(h*3600)+(m*60)+s;
                    #         }')
                    #         #echo $movie_start_time_unix
                    #         ################################
                    #         # 特徴点の動画ファイルでの秒数を算出
                    #         ################################
                    #         export_time_sec=$(basename "${kill_clip_file}" | sed -e 's/.jpg//g' | awk -F[_] '{print $NF}')

                    #         this_export_time_unix=$(echo "scale=0; $movie_start_time_unix + $export_time_sec" | bc | sed 's/^\./0./' | sed -e 's/\..*//g')
                    #         ################################
                    #         # csvファイルを出力
                    #         ################################
                    #         echo "$this_export_time_unix $export_time_sec $movie_file $type ocr" >> "$export_csv_file_ocr_work"
                    #         echo "          Record: $export_time_sec,$movie_file ($this_export_time_unix - $movie_start_time_unix) [$kill_clip_file]" >> "${export_csv_dir}/${log}"
                    #         echo "          Record: $export_time_sec,$movie_file ($this_export_time_unix - $movie_start_time_unix) [$kill_clip_file]"

                    #     done
                    # fi
                else
                    echo "      directory ${ocr_dir}/${movie_export_dirname} does not exist."
                fi
            done
        done
    done
done

cat "$export_csv_file_ocr_work" "$export_csv_file_cam_work" | uniq | sort -n | grep -v -E '^-' > "$export_csv_file_work"
cp "$export_csv_file_work" "$export_csv_file"

echo "Export csv:" >> "${export_csv_dir}/${log}"

cat "$export_csv_file" >> "${export_csv_dir}/${log}"

echo "----------------------------------------------"
echo "Export kill clip:"
echo "Export kill clip:" >> "${export_csv_dir}/${log}"

# export_file=`cat $export_csv_file | sed -e 's/,/ /g'`

while read row; do
    read this_unix_time this_export_point this_src_file this_type rec <<< $(awk '{print $1,$2,$3,$4,$5}' <<< $row )
    if [ -z "$this_unix_time" -o -z "$this_export_point" -o -z "$this_src_file" -o -z "$this_type" ]; then
        echo "  [ERROR]parse csv file error: $row"
        echo "  [ERROR]parse csv file error: $row" >> "${export_csv_dir}/${log}"
        exit 1
    fi
    echo "  process line: this_unix_time: $this_unix_time this_export_point: $this_export_point this_src_file: $this_src_file this_type: $this_type last_unix_time: $last_unix_time last_export_point: $last_export_point last_src_file: $last_src_file last_type: $last_type" >> "${export_csv_dir}/${log}"
    if [ -z "$last_src_file" ]; then
        echo "    init param"
        echo "    init param" >> "${export_csv_dir}/${log}"
        last_unix_time=$this_unix_time
        last_export_point=$this_export_point
        last_src_file=$this_src_file
        last_type=$this_type
    fi
    if [ "$this_src_file" != "$last_src_file" ] || [ "$this_src_file" = "$last_src_file" -a $((this_unix_time-last_unix_time)) -gt $battle_duration ]; then
        echo "    Start clip creation process:"
        echo "    Start clip creation process:" >> "${export_csv_dir}/${log}"
        if [ -n "$start_time" ]; then
            echo "      param start_time exists: ($start_time)" >> "${export_csv_dir}/${log}"
            if [ "$last_type" = "champion" ]; then
                this_start_time=$(echo "scale=1; $start_time - $champion_duration + 4" | bc | sed 's/^\./0./' )
            elif [ "$last_type" = "death" ]; then
                this_start_time=$(echo "scale=1; $start_time - $death_duration + 4" | bc | sed 's/^\./0./' )
            else
                this_start_time=$(echo "scale=1; $start_time - $movie_duration + 4" | bc | sed 's/^\./0./' )
            fi
            if [ "$this_type" == "blackhole" ]; then
                this_duration=$blackhole_duration
            elif [ "$this_type" == "death" ]; then
                # this_duration=$death_duration
                this_duration=$(echo "scale=1; $last_export_point - $this_start_time + 4" | bc | sed 's/^\./0./' )
            else
                this_duration=$(echo "scale=1; $last_export_point - $this_start_time + 4" | bc | sed 's/^\./0./')
            fi
            echo "      show variables: start_time: $start_time | this_duration: $this_duration | this_start_time: $this_start_time | last_export_point: $last_export_point" >> "${export_csv_dir}/${log}"
            echo "      show variables: start_time: $start_time | this_duration: $this_duration | this_start_time: $this_start_time | last_export_point: $last_export_point"
        else
            echo "      param start_time does not exist:"
            echo "      param start_time does not exist:" >> "${export_csv_dir}/${log}"
            if [ "$last_type" = "champion" ]; then
                this_start_time=$(echo "scale=1; $last_export_point - $champion_duration + 4" | bc | sed 's/^\./0./' )
                this_duration=$champion_duration
            elif [ "$last_type" = "death" ]; then
                this_start_time=$(echo "scale=1; $last_export_point - $death_duration + 4" | bc | sed 's/^\./0./' )
                this_duration=$death_duration
                # this_duration=`echo "scale=1; $last_export_point - $this_start_time + 4" | bc | sed 's/^\./0./'`
            else
                this_start_time=$(echo "scale=1; $last_export_point - $movie_duration + 4" | bc | sed 's/^\./0./' )
                if [ "$this_type" == "blackhole" ]; then
                    this_duration=$blackhole_duration
                elif [ "$this_type" == "death" ]; then
                    this_duration=$death_duration
                    # this_duration=`echo "scale=1; $last_export_point - $this_start_time + 4" | bc | sed 's/^\./0./'`
                else
                    this_duration=$movie_duration
                fi
            fi
            echo "      show variables: start_time: $start_time | this_duration: $this_duration | this_start_time: $this_start_time | last_export_point: $last_export_point" >> "${export_csv_dir}/${log}"
            echo "      show variables: start_time: $start_time | this_duration: $this_duration | this_start_time: $this_start_time | last_export_point: $last_export_point"
        fi

        this_basefilename=$(basename "$last_src_file" | awk -F[.] '{print $1}')_${this_start_time}_${rec}

        # type=knockが最終抽出点の場合，録画時間を10秒延長する
        if [ "$last_type" = "knock" ]; then
            # this_duration=$((this_duration+10))
            this_duration=$(echo "scale=1; $this_duration + 10" | bc | sed 's/^\./0./')
            this_save_file=${export_csv_local_dir}/${this_unix_time}_${last_type}_${this_basefilename}.mp4
        else
            this_save_file=${export_csv_local_dir}/${this_unix_time}_${last_type}_killfinish_${this_basefilename}.mp4
        fi


        if [ $(find "${export_csv_local_dir}" -name "${this_unix_time}_*" | wc -l) -eq 0 ] && [ $(find "${export_csv_local_dir}" -name "*_${this_basefilename}.mp4" | wc -l) -eq 0 ] && [ ! -f "${this_save_file}" ]; then
            echo "      Exec: kill_clip $last_src_file $this_start_time $this_duration $this_save_file"
            echo "      Exec: kill_clip $last_src_file $this_start_time $this_duration $this_save_file" >> "${export_csv_dir}/${log}"
            echo "kill_clip $last_src_file $this_start_time $this_duration $this_save_file" >> "${ffmpeg_command}"
        else
            echo "      Skip create ${this_save_file} (already exists)"
            echo "      Skip create ${this_save_file} (already exists)" >> "${export_csv_dir}/${log}"
        fi
        start_time=$this_export_point
    elif [ "$this_src_file" = "$last_src_file" -a $((this_unix_time-last_unix_time)) -le $battle_duration ]; then
        if [ -z "$start_time" ]; then
            start_time=$this_export_point
        fi
    else
        start_time=$this_export_point
    fi

    last_unix_time=$this_unix_time
    last_export_point=$this_export_point
    last_src_file=$this_src_file
    last_type=$this_type

done < "$export_csv_file"

echo "----------------------------------------------"
echo "    Start clip creation process(final loop):"
echo "    Start clip creation process(final loop):" >> "${export_csv_dir}/${log}"
if [ -n "$start_time" ]; then
    echo "      param start_time exists: ($start_time)"
    echo "      param start_time exists: ($start_time)" >> "${export_csv_dir}/${log}"
    if [ "$this_type" = "champion" ]; then
        this_start_time=$(echo "scale=1; $start_time - $champion_duration + 4" | bc | sed 's/^\./0./' )
    elif [ "$last_type" = "death" ]; then
        this_start_time=$(echo "scale=1; $start_time - $death_duration + 4" | bc | sed 's/^\./0./' )
    else
        this_start_time=$(echo "scale=1; $start_time - $movie_duration + 4" | bc | sed 's/^\./0./' )
    fi
    if [ $this_type == "blackhole" ]; then
        this_duration=$blackhole_duration
    # elif [ $this_type == "death" ]; then
    #     this_duration=$death_duration
    else
        this_duration=$(echo "scale=1; $last_export_point - $this_start_time + 4" | bc | sed 's/^\./0./')
    fi
    echo "      show variables: start_time: $start_time | this_duration: $this_duration | this_start_time: $this_start_time | last_export_point: $last_export_point" >> "${export_csv_dir}/${log}"
    echo "      show variables: start_time: $start_time | this_duration: $this_duration | this_start_time: $this_start_time | last_export_point: $last_export_point"
else
    echo "      param start_time does not exist:"
    echo "      param start_time does not exist:" >> "${export_csv_dir}/${log}"
    if [ "$this_type" = "champion" ]; then
        this_start_time=$(echo "scale=1; $this_export_point - $champion_duration + 4" | bc | sed 's/^\./0./' )
        this_duration=$champion_duration
    elif [ "$last_type" = "death" ]; then
        this_start_time=$(echo "scale=1; $this_export_point - $death_duration + 4" | bc | sed 's/^\./0./' )
        this_duration=$death_duration
    else
        this_start_time=$(echo "scale=1; $this_export_point - $movie_duration + 4" | bc | sed 's/^\./0./' )

        if [ $this_type == "blackhole" ]; then
            this_duration=$blackhole_duration
        elif [ $this_type == "death" ]; then
            this_duration=$death_duration
        else
            this_duration=$movie_duration
        fi
    fi
    echo "      show variables: start_time: $start_time | this_duration: $this_duration | this_start_time: $this_start_time | last_export_point: $last_export_point" >> "${export_csv_dir}/${log}"
    echo "      show variables: start_time: $start_time | this_duration: $this_duration | this_start_time: $this_start_time | last_export_point: $last_export_point"
fi

# type=knockが最終抽出点の場合，録画時間を10秒延長する
if [ "$last_type" = "knock" ]; then
    # this_duration=$((this_duration+10))
    this_duration=$(echo "scale=1; $this_duration + 10" | bc | sed 's/^\./0./')
    this_filename=${this_unix_time}_${this_type}_$(basename "$last_src_file" | awk -F[.] '{print $1}')_${this_start_time}_${rec}.mp4
    this_save_file=${export_csv_local_dir}/${this_filename}
else
    this_filename=${this_unix_time}_${this_type}_killfinish_$(basename "$last_src_file" | awk -F[.] '{print $1}')_${this_start_time}_${rec}.mp4
    this_save_file=${export_csv_local_dir}/${this_filename}
fi


is_exist=$(find "${export_csv_local_dir}" -name "${this_filename}")

if [ -z "${is_exist}" ]; then
    echo "      Exec: kill_clip $last_src_file $this_start_time $this_duration $this_save_file"
    echo "      Exec: kill_clip $last_src_file $this_start_time $this_duration $this_save_file" >> "${export_csv_dir}/${log}"
    echo "kill_clip $last_src_file $this_start_time $this_duration $this_save_file" >> "${ffmpeg_command}"
else
    echo "  Skip create ${this_save_file} (already exists)"
    echo "  Skip create ${this_save_file} (already exists)" >> "${export_csv_dir}/${log}"
fi

echo "----------------------------------------------"
echo "Now start exec ffmpeg_list:"
if "$REVERT"; then
    cat "${ffmpeg_command}" | sort -r > ./backup_file
    cp ./backup_file "${ffmpeg_command}"
else
    cat "${ffmpeg_command}" | sort -R > ./backup_file
    cp ./backup_file "${ffmpeg_command}"
fi
cat "${ffmpeg_command}"
cmd_file='./command.sh'


# audioの処理

OLDIFS=$IFS
# IFSをカンマに設定して文字列を分割
IFS=',' read -ra elements <<< "$audio"

AUDIO_ARGS=""

# 配列の要素を表示
for element in "${elements[@]}"; do
    echo "$element"
    echo " -map 0:a:${element}"
    AUDIO_ARGS=" -map 0:a:${element} ${AUDIO_ARGS}"
done
IFS=$OLDIFS

cat <<EOF > $cmd_file
#!/bin/bash

set -x

ffmpeg_out=${export_csv_work_dir}
mkdir -p \${ffmpeg_out}

kill_clip () {

    echo "    last_src_file: \$1"
    echo "    this_start_time: \$2"
    echo "    this_duration: \$3"
    echo "    this_save_file: \$4"

    local file_kill_clip=\${ffmpeg_out}/out.mp4

    rm -f \${file_kill_clip}
    i=0
    while :; do
        echo "      ffmpeg trial in kill_clip: \$i"
        ffmpeg -y -ss \$2 -i \$1 -t \$3 -vcodec libx264 -acodec libmp3lame -vsync 1 -async 1000 -map 0:v:0 ${AUDIO_ARGS} \${file_kill_clip} </dev/null 2>&1
        [[ \`ls -l \${file_kill_clip} | awk '{print \$5}'\` -gt 262 ]] && break
        i=\$(expr \$i + 1)
        [[ i -eq 5 ]] && break
    done

    ls -l \${file_kill_clip}
    mv \${file_kill_clip} \$4
    ls -l \$this_save_file
}

EOF

cat "${ffmpeg_command}" >> $cmd_file

chmod +x $cmd_file

echo "-----------------------"
echo "command_file:"
cat $cmd_file
echo "-----------------------"

$cmd_file
