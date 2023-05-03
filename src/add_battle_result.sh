#!/bin/bash

#set -x

# out=/root/out

#############################
PROGNAME=$(basename $0)
VERSION="0.21"
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
        '--debug' )
            DEBUG_MODE=true
            shift 1
            ;;
        '-a'|'--audio' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            AUDIO_CHANNEL="$2"
            shift 2
            ;;
        '-m'|'--movie' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            movie_file="$2"
            shift 2
            ;;
        '-o'|'--out' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            out_dir="$2"
            shift 2
            ;;
        '-p'|'--picture' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            picture_dir="$2"
            shift 2
            ;;
        '--work' )
            if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                exit 1
            fi
            work_dir="$2"
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

result_flg_log=${work_dir}/'flg_add_result.log'

if [ -z "$movie_file" -o -z "$picture_dir" ]; then
    echo "    param -m and -p is required." >> "$result_flg_log"
    exit 1
fi

movie_dir=$(dirname "$movie_file")

if [ -z "$out_dir" ]; then
    out_dir=$movie_dir
fi

apex_tracker_dir=${apex_tracker_dir:-/root}


for match in $(ls "$picture_dir" | grep match | grep -v .log)
do
    echo "    Start analyze ${match}:" >> $result_flg_log
    echo "    Start analyze ${match}:"
    result_files=$(find "$picture_dir/${match}"/result -name *result*jpg)
    #echo $movie_file
    #echo $result_files
    unset rank tkill kill damage
    for result_file in $result_files
    do
        echo "      Check result file ${result_file}:" >> "$result_flg_log"
        echo "      Check result file ${result_file}:"
        #this_result=`python3 $apex_tracker_dir/ocr/apex-result.py $result_file`
        read this_rank this_tkill this_kill this_damage <<< $( python3 "$apex_tracker_dir"/apex-result.py "$result_file" | awk -F@ '{print $1, $2, $3, $4}')
        if [ "$this_rank" != "null" ]; then
            if [ "$this_rank" -gt 20 ]; then
                # OCR出力値が20より大きい場合，誤検知のため先頭1桁のみを出力
                rank=${this_rank:0:1}
                echo "        Fix rank to $rank (actual: $this_rank)" >> "$result_flg_log"
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
    echo "      result: rank=${rank} tkill=${tkill} kill=${kill} damage=${damage}" >> "$result_flg_log"
    echo "      result: rank=${rank} tkill=${tkill} kill=${kill} damage=${damage}"
    movie_filename=$(basename "$movie_file")
    new_movie_filename=$(echo "$movie_filename" | awk -F[.] '{print $1}' | sed -r 's/(.*match[0-9])_(.*)/\1/g')
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
    echo "      $new_movie_filename" >> "$result_flg_log"
    echo "mv $movie_dir/$movie_filename $out_dir/$new_movie_filename"
    mv "$movie_dir/$movie_filename" "$out_dir/$new_movie_filename"
done
