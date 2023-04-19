#!/bin/bash

# set -e

#############################
PROGNAME=$(basename $0)
VERSION="0.21"
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
        '-b'|'--battle' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            battle_clip_directory=$2
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
        '-s'|'--save' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            save_dir=$2
            shift 2
            ;;
        '-w'|'--work' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            work_directory=$2
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


out_dir=${out_dir:="/Volumes/SSD-PGU3/GameRecs/apex"}
apex_tracker_dir=${apex_tracker_dir:=/root}

movie_directory=`echo $movie_directory | sed -e 's/\/$//g'`
ocr_whole_dir=`echo $ocr_whole_dir | sed -e 's/\/$//g'`

echo OCR directory: $ocr_whole_dir

csv_flg='flg_csv_exported'
result_flg='flg_result_exported'
csv_flg_log='flg_csv.log'
result_flg_log='flg_result.log'

echo "MODE: $mode"

if [ $mode == "csv" ]; then
    for ocr_dir in `find ${ocr_whole_dir} -type d -depth 1`
    do
        if [ ! -f ${ocr_dir}/${csv_flg} ]; then
            # 動画の長さを計算
            #movie_length=`ffmpeg -i $movie_file 2>&1 | grep -m 1 DURATION | awk '{print $3}'`
            # 動画の録画開始時刻を取得
            #movie_start=`basename $movie_directory | awk -F[.] '{print $1}'`
            ocr_final=`/usr/local/bin/gls --time-style=full-iso -l $ocr_dir/match*/*/ | grep jpg | awk '{print $6 $7}' | sed -e 's/-//g' | sed -e 's/://g' | sort -r | head -n 1 | cut -c 1-14`
            ocr_start=`basename $ocr_dir | sed -e 's/-//g' | sed -e 's/_//g'`
            echo $ocr_start-$ocr_final
            echo $ocr_start-$ocr_final >> ${ocr_dir}/${csv_flg_log}

            echo "Create csv file"
            echo "Create csv file" >> ${ocr_dir}/${csv_flg_log}
            for movie_directory in `echo $movie_directories | sed -e 's/,/ /g'`
            do
                echo Movie directory: $movie_directory
                ls $movie_directory/*.m*
                for movie_file in `ls $movie_directory/*.m*`
                do
                    echo "  movie_file: $movie_file"
                    echo "  movie_file: $movie_file" >> ${ocr_dir}/${csv_flg_log}
                    movie_date=`echo $movie_file | xargs basename | awk -F[.] '{print $1}' | sed -e 's/-//g' | sed -e 's/://g' | sed -e 's/_//g' `
                    echo movie_date: $movie_date
                    echo movie_date: $movie_date >> ${ocr_dir}/${csv_flg_log}
                    if [ $(( $ocr_final - $movie_date )) -gt 0 -a $(( $movie_date - $ocr_start )) -gt 0 ]; then
                        echo Hit $movie_file
                        echo Hit $movie_file >> ${ocr_dir}/${csv_flg_log}
                        movie_export_dirname=`basename $movie_file | awk -F[.] '{print $1}'`
                        mkdir -p ${out_dir}/${movie_export_dirname}
                        rm -f ${out_dir}/${movie_export_dirname}/*flg*
                        echo "  Execute apex-rec.sh"
                        echo "  Execute apex-rec.sh" >> ${ocr_dir}/${csv_flg_log}
                        echo "    movie_file: $movie_file"
                        echo "    movie_file: $movie_file" >> ${ocr_dir}/${csv_flg_log}
                        echo "    ocr_dir: $ocr_dir"
                        echo "    ocr_dir: $ocr_dir" >> ${ocr_dir}/${csv_flg_log}
                        echo "    out_dir: $out_dir"
                        echo "    out_dir: $out_dir" >> ${ocr_dir}/${csv_flg_log}
                        echo "    exec ${apex_tracker_dir}/ocr/apex-rec.sh -m $movie_file -o $ocr_dir -d $out_dir" >> ${ocr_dir}/${csv_flg_log}
                        ${apex_tracker_dir}/ocr/apex-rec.sh -m $movie_file -o $ocr_dir -d $out_dir
                    fi
                done
            done
            touch ${ocr_dir}/${csv_flg}
        else
            echo "  Skip create csv : ${ocr_dir}"
            echo "  Skip create csv : ${ocr_dir}" >> ${ocr_dir}/${csv_flg_log}
        fi
    done
fi

if [ $mode == "result" ]; then
    for battle_clip_file in `ls ${battle_clip_directory}/*match*.mp4`
    do
        echo "  Add result to battle clip file: $battle_clip_file"
        clip_date=`basename $battle_clip_file | awk -F[_] '{printf("%s_%s",$1,$2)}'`
        match=`basename $battle_clip_file | awk -F[_.] '{print $3}'`
        target_ocr_directory=`find ${ocr_whole_dir} -maxdepth 1 -type d -name "${clip_date}"`
        this_match_flg=${work_directory}/${clip_date}/${match}_${result_flg}
        echo "    clip_date: ${clip_date}"
        echo "    match: ${match}"
        echo "    target_ocr_directory: ${target_ocr_directory}"
        if [ -d ${target_ocr_directory}/${match} ]; then
            if [ ! -f $this_match_flg ]; then
                picture_dir=${target_ocr_directory}
                movie_file=${battle_clip_file}
                work_dir=${work_directory}

                result_flg_log=${work_dir}/'flg_add_result.log'

                movie_dir=`dirname $movie_file`

                if [ -z "$out_dir" ]; then
                    out_dir=$movie_dir
                fi


                apex_tracker_dir=${apex_tracker_dir:-/root}
                echo "    debug text"
                echo "    Start analyze ${match}:" >> $result_flg_log
                echo "    Start analyze ${match}:"
                result_files=`find $picture_dir/${match}/result -name *result*jpg`
                unset rank tkill kill damage
                for result_file in $result_files
                do
                    echo "      Check result file ${result_file}:" >> $result_flg_log
                    echo "      Check result file ${result_file}:"
                    read this_rank this_tkill this_kill this_damage <<< $( python3 $apex_tracker_dir/apex-result.py $result_file | awk -F@ '{print $1, $2, $3, $4}')
                    if [ "$this_rank" != "null" ]; then
                        if [ $this_rank -gt 20 ]; then
                            # OCR出力値が20より大きい場合，誤検知のため先頭1桁のみを出力
                            rank=${this_rank:0:1}
                            echo "        Fix rank to $rank (actual: $this_rank)" >> $result_flg_log
                            echo "        Fix rank to $rank (actual: $this_rank)"
                        else
                            rank=$this_rank
                        fi
                    fi
                    if [ "$this_tkill" != "null" ]; then
                        tkill=$this_tkill
                    fi
                    if [ "$this_kill" != "null" ]; then
                        kill=$this_kill
                    fi
                    if [ "$this_damage" != "null" ]; then
                        damage=$this_damage
                    fi
                done
                echo "      result: rank=${rank} tkill=${tkill} kill=${kill} damage=${damage}" >> $result_flg_log
                echo "      result: rank=${rank} tkill=${tkill} kill=${kill} damage=${damage}"
                movie_filename=`basename $movie_file`
                new_movie_filename=`echo $movie_filename | awk -F[.] '{print $1}' | sed -r 's/(.*match[0-9])_(.*)/\1/g'`
                if [ -n "$rank" ]; then
                    new_movie_filename=${new_movie_filename}"_rank_"$rank
                fi
                if [ -n "$tkill" ]; then
                    new_movie_filename=${new_movie_filename}"_teamkill_"$tkill
                fi
                if [ -n "$kill" ]; then
                    new_movie_filename=${new_movie_filename}"_kill_"$kill
                fi
                if [ -n "$damage" ]; then
                    new_movie_filename=${new_movie_filename}"_damage_"$damage
                fi
                new_movie_filename=${new_movie_filename}".mp4"
                echo "      $new_movie_filename" >> $result_flg_log
                echo "      mv $movie_dir/$movie_filename $out_dir/$new_movie_filename"
                mv $movie_dir/$movie_filename $out_dir/$new_movie_filename

                touch $this_match_flg
            else
                echo "    Skip adding result for ${target_ocr_directory}/${match}"
            fi
        else
            echo "  match ${match} directory does not found in ${target_ocr_directory}/${match}"
        fi
    done
fi