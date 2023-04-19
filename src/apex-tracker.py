import pathlib
import os
import subprocess
import csv
import numpy as np
import cv2
import tensorflow as tf
from tqdm import tqdm
import argparse
import shutil
parser = argparse.ArgumentParser()
parser.add_argument("src", type=str,
                    help="Target file")
parser.add_argument("--skiptf", action="store_true",
                    help="Target file path")
parser.add_argument("--battle", action="store_true",
                    help="Target file path")
parser.add_argument("--result", action="store_true",
                    help="Target file path")
parser.add_argument("--debug", action="store_true",
                    help="Debug mode")
parser.add_argument("-o", "--output", type=str,default='/root/src_movie/export',
                    help="Export path")
parser.add_argument("--audio", type=str,
                    help="Audio Channel[Optional]")

args = parser.parse_args()

# 切り出し元動画パス
src_movie = args.src
basename = os.path.splitext(os.path.basename(src_movie))[0]

# ファイル出力先のパスを指定
export_path = args.output

# pythonプログラムのディレクトリを確認
p = pathlib.Path(os.path.dirname(__file__))
program_path = str(p.resolve())

# モデルファイルパス
model_path = program_path + '/model/model.tflite'

# debugディレクトリ
debug_dir = export_path + '/' + basename+ '/' + basename + '_debug'

if args.debug:
    os.makedirs(debug_dir, exist_ok=True)

# battleディレクトリ
battle_dir = export_path + '/' + basename+ '/' + basename + '_battle'

# resultディレクトリ
result_dir = export_path + '/' + basename + '_result'

# csvファイルの定義
cut_time_battle_csv = export_path + '/' + basename+ '/' + basename + '_cut_time_battle.csv'
cut_time_result_csv = export_path + '/' + basename+ '/' + basename + '_cut_time_result.csv'

# src_movie = 'src_movie/sample.mkv'
# 切り出し秒数
cut_duration = 1
cut_duration_battle = 12
# 切り出し終了時間からこの秒数は切り出し開始しない
death_duration_battle = 8
death_duration = 16

interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("apex-tracker.py with option: ",args)



if not args.skiptf:
    if args.battle:
        # 書き出しCSVファイル
        with open(cut_time_battle_csv, 'w') as f:
            writer = csv.writer(f)
            # 動画を読み込む
            cap = cv2.VideoCapture(src_movie)
            # フレーム数を取得
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            # 1秒あたりフレーム数を取得
            fps = cap.get(cv2.CAP_PROP_FPS)
            # 0.5秒に1回予測する
            skip = fps / 2
            # フレーム
            i = 0
            # 切り出し開始しないカウントダウン
            no_start = 0
            for i in tqdm(range(frame_count)):
                ret, img = cap.read()
                if ret:
                    if i % skip == 0 and no_start == 0:
                        # フレームを予測する大きさに縮小
                        shrink = cv2.resize(
                            img, (224, 224), interpolation=cv2.INTER_CUBIC)
                        # 4次元に変換する
                        input_tensor = shrink.reshape(1, 224, 224, 3)
                        # それをTensorFlow liteに指定する
                        interpreter.set_tensor(input_details[0]['index'], input_tensor)
                        # 推論実行
                        interpreter.invoke()
                        # 出力層を確認
                        output_tensor = interpreter.get_tensor(output_details[0]['index'])
                        # やられたシーン判定
                        scene = np.argmax(output_tensor)
                        if scene == 4 or scene == 5 or scene == 0:
                            # やられたシーンの時は
                            # 切り出し開始秒数を出力
                            ss = i - cut_duration_battle * fps
                            if ss < 0:
                                ss = 0
                            writer.writerow(["%d.%02d" % (ss/fps, 100 * (ss % fps)/fps),scene])
                            # シーン判定をしばらく止める
                            no_start = fps * death_duration_battle
                    if no_start >= 1:
                        no_start -= 1
                else:
                    break

    if args.result:
        # 書き出しCSVファイル
        with open(cut_time_result_csv, 'w') as f:
            writer = csv.writer(f)
            # 動画を読み込む
            cap = cv2.VideoCapture(src_movie)
            # フレーム数を取得
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            # 1秒あたりフレーム数を取得
            fps = cap.get(cv2.CAP_PROP_FPS)
            # 0.5秒に1回予測する
            skip = fps / 2
            # フレーム
            i = 0
            # 切り出し開始しないカウントダウン
            no_start = 0
            for i in tqdm(range(frame_count)):
                ret, img = cap.read()
                if ret:
                    if i % skip == 0 and no_start == 0:
                        # フレームを予測する大きさに縮小
                        shrink = cv2.resize(
                            img, (224, 224), interpolation=cv2.INTER_CUBIC)
                        # 4次元に変換する
                        input_tensor = shrink.reshape(1, 224, 224, 3)
                        # それをTensorFlow liteに指定する
                        interpreter.set_tensor(input_details[0]['index'], input_tensor)
                        # 推論実行
                        interpreter.invoke()
                        # 出力層を確認
                        output_tensor = interpreter.get_tensor(output_details[0]['index'])
                        # やられたシーン判定
                        scene = np.argmax(output_tensor)
                        if scene == 0 or scene == 1 or scene == 6:
                            # やられたシーンの時は
                            # 切り出し開始秒数を出力
                            ss = i
                            if ss < 0:
                                ss = 0
                            writer.writerow(["%d.%02d" % (ss/fps, 100 * (ss % fps)/fps),scene])
                            # シーン判定をしばらく止める
                            no_start = fps * death_duration
                    if no_start >= 1:
                        no_start -= 1
                else:
                    break

scenedef=['result','memberlist','deathprotection','other','enemy','death','map']

if args.debug:
    sss = []
    ttt = []
    print('debug in apex-tracker.py')
    with open(cut_time_battle_csv) as f:
        reader = csv.reader(f)
        for row in reader:
            sss.append(row[0])
            ttt.append(row[1])

    for i in tqdm(range(len(sss))):
        ss = sss[i]
        point = float(ss) + float(cut_duration_battle)
        print('Export debug scene', i, 'from', point, 'from', src_movie)
        command = "ffmpeg -y -ss %f -t %f -i %s -frames:v 1 -f image2 \"%s/%s_%s_%s.jpg\"" % (point , point , src_movie, debug_dir, basename, scenedef[int(ttt[i])], float(point) - 12.0 )
        subprocess.run(command, shell=True)

if args.battle and not args.debug:
    shutil.rmtree(battle_dir, ignore_errors=True)
    os.makedirs(battle_dir, exist_ok=True)
    battle_write_log_path = battle_dir+'/write.log'
    with open(battle_write_log_path, mode='w') as logfile:
        cont_duration = 120
        before_scene_sec = 60
        sss = []
        scene = []
        with open(cut_time_battle_csv) as f:
            reader = csv.reader(f)
            for row in reader:
                sss.append(row[0])
                scene.append(row[1])
        start = sss[0]
        end = sss[0]
        current = 0
        for i in tqdm(range(len(sss))):
            ss = sss[i]
            if (float(ss) - float(end) >= cont_duration or int(scene[i]) == 5 or int(scene[i]) == 0 ) and not start == -1:
                if int(scene[i]) == 5 or int(scene[i]) == 0:
                    end = float(ss)
                log = "  [DEBUG] export battle movie: ss:%s start:%s end:%s scene:%s" % (ss,start,end,scene[i])
                print(log)
                logfile.write(log+'\n')
                # ssが部隊全滅の場合，動画を短くする．そうで無い場合は，長めに40秒記録．
                if int(scene[i]) == 5 or int(scene[i]) == 0:
                    log = "  [DEBUG]   condition: team eliminated: ss:%s start:%s end:%s scene:%s" % (ss,start,end,scene[i])
                    print(log)
                    logfile.write(log+'\n')
                    duration = float(end) - float(start) + cut_duration_battle + before_scene_sec
                    start = float(end) - float(duration) + cut_duration_battle 
                    if float(current) > float(start):
                        duration = float(duration) - ( float(current) - float(start) )
                        start = current
                    current = float(start) + float(duration)
                else:
                    log = "  [DEBUG]   condition: team alive: ss:%s start:%s end:%s scene:%s" % (ss,start,end,scene[i])
                    print(log)
                    logfile.write(log+'\n')
                    duration = float(end) - float(start) + cut_duration_battle + before_scene_sec
                    start = float(start)  - float(cut_duration_battle) - 10.0
                    if float(current) > float(start):
                        duration = float(duration) - ( float(current) - float(start) )
                        start = current
                    current = float(start) + float(duration)
                log = "Export battle scene %d from %f sec for %f sec from %s" % (i,start,duration,src_movie)
                print(log)
                logfile.write(log+'\n')
                if args.audio:
                    command = "ffmpeg -y -ss %s -i %s -t %d -map 0:v:0 -vcodec libx264 -map 0:a:%s -acodec copy \"%s/%s_battle%03d.mp4\"" % (start, src_movie, duration, args.audio ,battle_dir, basename, i)
                else:
                    command = "ffmpeg -y -ss %s -i %s -t %d -c copy \"%s/%s_battle%03d.mp4\"" % (start, src_movie, duration, battle_dir, basename, i)
                log = "  [DEBUG] ffmpeg command: %s" % (command)
                print(log)
                logfile.write(log+'\n')
                subprocess.run(command, shell=True)
                if int(scene[i]) == 5 or int(scene[i]) == 0:
                    start = -1
                else:
                    start = float(ss)
                end = ss
            else:
                end = ss
                if start == -1 and not ( int(scene[i]) == 5 or int(scene[i]) == 0 ):
                    start = float(ss)
            log = "  [DEBUG] ss:%s start:%s end:%s scene:%s" % (ss, start, end, scene[i])
            print(log)
            logfile.write(log+'\n')
        if not start == -1:
            duration = float(end) - float(start) + 5 + cut_duration_battle 
            log = "Export battle scene %d from %f sec for %f sec from %s" % (i,start,duration,src_movie)
            print(log)
            logfile.write(log+'\n')
            if args.audio:
                command = "ffmpeg -y -ss %s -i %s -t %d -map 0:v:0 -vcodec libx264 -map 0:a:%s -acodec copy \"%s/%s_battle%03d.mp4\"" % (start, src_movie, duration, args.audio ,battle_dir, basename, i)
            else:
                command = "ffmpeg -y -ss %s -i %s -t %d -c copy \"%s/%s_battle%03d.mp4\"" % (start, src_movie, duration, battle_dir, basename, i)
            log = "  [DEBUG] ffmpeg command: %s" % (command)
            print(log)
            logfile.write(log+'\n')
            subprocess.run(command, shell=True)
        logfile.close

if args.result:
    shutil.rmtree(result_dir, ignore_errors=True)
    os.makedirs(result_dir, exist_ok=True)
    sss = []
    ttt = []
    with open(cut_time_result_csv) as f:
        reader = csv.reader(f)
        for row in reader:
            sss.append(row[0])
            ttt.append(row[1])

    for i in tqdm(range(len(sss))):
        ss = sss[i]
        print('Export result scene', i, 'from', ss, 'from', src_movie)
        if int(ttt[i]) == 1:
            command = "ffmpeg -y -ss %f -t %f -i %s -pix_fmt yuvj422p -deinterlace -frames:v 1 -f mjpeg \"%s/%s_result%03d_%s_%s.jpg\"" % (float(ss) + 0.1 , float(ss) + 0.1, src_movie, result_dir, basename, int(i), scenedef[int(ttt[i])],float(ss))
        else:
            command = "ffmpeg -y -ss %f -t %f -i %s -pix_fmt yuvj422p -deinterlace -frames:v 1 -f mjpeg \"%s/%s_result%03d_%s_%s.jpg\"" % (float(ss) + 0.1 , float(ss) + 0.1, src_movie, result_dir, basename, int(i), scenedef[int(ttt[i])],float(ss))
        subprocess.run(command, shell=True)

