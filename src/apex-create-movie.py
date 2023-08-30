import pathlib
import os
import subprocess
import csv
import numpy as np
import cv2
from tqdm import tqdm
import argparse
import shutil
parser = argparse.ArgumentParser()
parser.add_argument("src", type=str,
                    help="Target file")
parser.add_argument("--battle", action="store_true",
                    help="Target file path")
parser.add_argument("--result", action="store_true",
                    help="Target file path")
parser.add_argument("--debug", action="store_true",
                    help="Debug mode")
parser.add_argument("--output", type=str,
                    default='/root/out',
                    help="Output path")
parser.add_argument("--ocr", type=str,
                    default='/root/ocr',
                    help="OCR path")
parser.add_argument("--work", type=str,
                    default='/root/work',
                    help="Work path")
parser.add_argument("-c", "--camlog", type=str,
                    help="apex cam log directory")
parser.add_argument("--audio", type=str,
                    help="Audio Channel[Optional]")

args = parser.parse_args()

# 切り出し元動画パス
src_movie = args.src
basename = os.path.splitext(os.path.basename(src_movie))[0]

# ファイル出力先のパスを指定
export_path = args.output
ocr_path = args.ocr
work_path = args.work

# pythonプログラムのディレクトリを確認
p = pathlib.Path(os.path.dirname(__file__))
program_path = str(p.resolve())

# debugディレクトリ
debug_dir = export_path + '/' + basename+ '/' + basename + '_debug'

if args.debug:
    os.makedirs(debug_dir, exist_ok=True)

# battleディレクトリ
battle_work_dir = work_path + '/' + basename

# csvファイルの定義
cut_time_battle_csv = ocr_path + '/' + basename+ '/' + 'cut_time_battle.csv'

# src_movie = 'src_movie/sample.mkv'
# 切り出し秒数
cut_duration_battle = 30
# マップ表示の抽出時間
cut_duration_map= 5
# リザルト、チャンピョン時の抽出時間
cut_duration_result = 15
# 切り出し終了時間からこの秒数は切り出し開始しない
death_duration_battle = 8
death_duration = 30
death_after_sec = 15
# 戦闘シーンの最低録画秒数
battle_min_rec = 60
battle_final_rec = 180
# 特徴点間を連結する場合の秒数
cont_duration = 60
# 特徴点より設定秒数だけ前から録画を開始
before_scene_sec = 3

print("    apex-create-movie.py with option: ",args)

scenedef=['result','memberlist','deathprotection','other','enemy','death','map']

os.makedirs(battle_work_dir, exist_ok=True)
battle_write_log_path = battle_work_dir+'/create_match_clip.log'
with open(battle_write_log_path, mode='w') as logfile:
    sss = []
    scene = []
    match = []

    is_csv_file = os.path.isfile(cut_time_battle_csv)
    if is_csv_file:
        if os.path.getsize(cut_time_battle_csv) != 0:
            with open(cut_time_battle_csv) as f:
                reader = csv.reader(f)
                for row in reader:
                    sss.append(row[0])
                    scene.append(row[1])
                    match.append(row[2])
            start = sss[0]
            end = sss[0]
            current = 0

            for i in tqdm(range(len(sss))):
                # 録画に含めたいシーンを指定[> 0:result / 1:memberlist / 2:deathprotection / 3:other / 4:enemy / 5:death / 8:kill / 9:champion / 10:map / 12: darkveil
                if int(scene[i]) == 1 or int(scene[i]) == 2 or int(scene[i]) == 4 or int(scene[i]) == 8 or int(scene[i]) == 5 or int(scene[i]) == 0 or int(scene[i]) == 3 or int(scene[i]) == 9 or int(scene[i]) == 10 or int(scene[i]) == 12:
                    ss = sss[i]
                    # start, endの更新処理
                    
                    # 録画区間を確定する条件をTrueとする
                    # if (float(ss) - float(end) >= cont_duration or int(scene[i]) == 5 or int(scene[i]) == 0 or int(scene[i]) == 9 or int(scene[i]) == 8):

                    #############
                    # endの更新
                    #############
                    
                    # 特徴点が戦闘の場合
                    if int(scene[i]) == 2 or int(scene[i]) == 4 or int(scene[i]) == 8 or int(scene[i]) == 12:
                        j=i+1
                        # csvファイルで、戦闘の特徴点が継続しているところまでを抽出
                        while len(sss) > j and (int(scene[j]) == 2 or int(scene[j]) == 4 or int(scene[j]) == 8 or int(scene[j]) == 12):
                            end = float(sss[j]) + float(cut_duration_battle)
                            j+=1
                    # 特徴点がリザルト画面、部隊全滅、チャンピョンの場合
                    elif int(scene[i]) == 0 or int(scene[i]) == 5 or int(scene[i]) == 9:
                        j=i+1
                        # csvファイルで、戦闘の特徴点が継続しているところまでを抽出
                        while len(sss) > j and (int(scene[j]) == 0 or int(scene[j]) == 5 or int(scene[j]) == 9):
                            end = float(sss[j]) + float(cut_duration_result)
                            j+=1
                    # 特徴点がマップの場合
                    elif int(scene[i]) == 10:
                        j=i+1
                        # csvファイルで、戦闘の特徴点が継続しているところまでを抽出
                        while len(sss) > j and (int(scene[j]) == 10):
                            end = float(sss[j]) + float(cut_duration_map)
                            j+=1
                    else:
                        end = float(end) + float(cut_duration_battle)

                    # クリップの時間durationを計算し、startを調整
                    # 全滅かチャンピョンの場合のみ、battle_final_recを利用.
                    if int(scene[i]) == 5 or int(scene[i]) == 9:
                        duration = max(float(end) - float(start) + before_scene_sec, battle_final_rec)
                    else:
                        duration = max(float(end) - float(start) + before_scene_sec, battle_min_rec)

                    # endを固定し、durationからstartを計算。ただし、前後のクリップで同じ時間を抽出しないように、current以前の時間をクリップしないように調整
                    start = float(end) - float(duration) - before_scene_sec
                    if float(current) > float(start):
                        duration = float(duration) - ( float(current) - float(start) )
                        start = current
                    current = float(start) + float(duration)

                    # durationが0以上の場合にクリップ生成処理
                    if duration != 0:
                        log = "Export battle scene %d from %f sec for %f sec from %s" % (i,start,duration,src_movie)
                        print(log)
                        logfile.write(log+'\n')

                        match_dir = battle_work_dir + '/match' + match[i] + '/rec'
                        # os.makedirs(match_dir, exist_ok=True)
                        os.makedirs(match_dir, exist_ok=True)
                        
                        if args.debug:
                            duration=5
                            log = "    [DEBUG] rec duration: %f " % (duration)
                            print(log)
                            logfile.write(log+'\n')

                        if args.audio:
                            command = "ffmpeg -y -ss %s -i \"%s\" -t %d -map 0:v:0 -vcodec libx264 -map 0:a:%s -acodec copy -vsync 1 -async 1000 \"%s/%s_battle%03d_%03dm%02ds-%03dm%02ds.mp4\" </dev/null 2>&1 </dev/null 2>&1" % (start, src_movie, duration, args.audio , match_dir, basename, i, int(float(start)) // 60, int(int(float(start)) % 60) ,int(float(start)+float(duration)) // 60, int(float(start)+float(duration)) % 60)
                        else:
                            command = "ffmpeg -y -ss %s -i \"%s\" -t %d -map 0:v:0 -vcodec libx264 -map 0:a:1 -map 0:a:2 -map 0:a:3 -vsync 1 -async 1000 \"%s/%s_battle%03d_%03dm%02ds-%03dm%02ds.mp4\" </dev/null 2>&1 </dev/null 2>&1" % (start, src_movie, duration, match_dir, basename, i, int(float(start)) // 60, int(int(float(start)) % 60) ,int(float(start)+float(duration)) // 60, int(float(start)+float(duration)) % 60)

                        log = "  [DEBUG] ffmpeg command: %s" % (command)
                        print(log)
                        logfile.write(log+'\n')
                        subprocess.run(command, shell=True)
                        # subprocess.run(command, shell=True,stdout = subprocess.DEVNULL,stderr = subprocess.DEVNULL)
                        subprocess.run('ls -al '+match_dir, shell=True,stdout = subprocess.DEVNULL,stderr = subprocess.DEVNULL)

                    if int(scene[i]) == 5 or int(scene[i]) == 0 or int(scene[i]) == 9 or int(scene[i]) == 8:
                        start = -1
                    else:
                        start = float(ss)
                    # end = ss
                    # else:
                    #     end = ss
                    #     if start == -1 and not ( int(scene[i]) == 5 or int(scene[i]) == 0 or int(scene[i]) == 9 or int(scene[i]) == 8):
                    #         start = float(ss)
                    #log = "  [DEBUG] ss:%s start:%s end:%s scene:%s" % (ss, start, end, scene[i])
                    #print(log)
                    #logfile.write(log+'\n')
            # csvファイルを一通り捜査した後の録画処理
            if not start == -1:
                end = float(end) + float(cut_duration_battle)
                duration = max(float(end) - float(start) + before_scene_sec, battle_min_rec)
                log = "Export battle scene %d from %.2f sec for %.2f sec from %s" % (int(i),float(start),float(duration),src_movie)
                print(log)
                match_dir = battle_work_dir + '/match' + match[i] + '/rec'
                os.makedirs(match_dir, exist_ok=True)
                # os.makedirs('/rec', exist_ok=True)
                logfile.write(log+'\n')

                if args.debug:
                    duration=5
                    log = "  [DEBUG] rec duration: %f " % (duration)
                    print(log)
                    logfile.write(log+'\n')

                if args.audio:
                    command = "ffmpeg -y -ss %s -i \"%s\" -t %d -map 0:v:0 -vcodec libx264 -map 0:a:%s -acodec copy -vsync 1 -async 1000 \"%s/%s_battle%03d_%03dm%02ds-%03dm%02ds.mp4\" </dev/null 2>&1 </dev/null 2>&1" % (start, src_movie, duration, args.audio ,match_dir, basename, i, int(float(start)) // 60, int(int(float(start)) % 60) ,int(float(start)+float(duration)) // 60, int(float(start)+float(duration)) % 60)
                else:
                    command = "ffmpeg -y -ss %s -i \"%s\" -t %d -map 0:v:0 -vcodec libx264 -map 0:a:1 -map 0:a:2 -map 0:a:3 -vsync 1 -async 1000 \"%s/%s_battle%03d_%03dm%02ds-%03dm%02ds.mp4\" </dev/null 2>&1 </dev/null 2>&1" % (start, src_movie, duration, match_dir, basename, i, int(float(start)) // 60, int(int(float(start)) % 60) ,int(float(start)+float(duration)) // 60, int(float(start)+float(duration)) % 60)
                log = "  [DEBUG] ffmpeg command: %s" % (command)
                print(log)
                logfile.write(log+'\n')
                subprocess.run(command, shell=True)
                subprocess.run('ls -al '+match_dir, shell=True,stdout = subprocess.DEVNULL,stderr = subprocess.DEVNULL)

            subprocess.run('ls -al '+match_dir, shell=True,stdout = subprocess.DEVNULL,stderr = subprocess.DEVNULL)
            #shutil.move('/rec', match_dir)

    logfile.close


