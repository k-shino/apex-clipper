import pathlib
import os
import subprocess
import csv
import numpy as np
import cv2
from tqdm import tqdm
import logging
from logging import StreamHandler, FileHandler, Formatter
from logging import INFO, DEBUG, NOTSET
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
parser.add_argument("--match", type=str,
                    help="Match number")

args = parser.parse_args()

scene_list=['result','memberlist','deathprotection','other','enemy','death','map','lobby','kill','champion','map','spectate','DARKEVIL','landing','startmatch']

# 切り出し元動画パス
src_movie = args.src
basename = os.path.splitext(os.path.basename(src_movie))[0]

# ファイル出力先のパスを指定
export_path = args.output
ocr_path = args.ocr
work_path = args.work

match_num=int(args.match)

# pythonプログラムのディレクトリを確認
p = pathlib.Path(os.path.dirname(__file__))
program_path = str(p.resolve())

# debugディレクトリ
debug_dir = export_path + '/' + basename+ '/' + basename + '_debug'

if args.debug:
    os.makedirs(debug_dir, exist_ok=True)

# battleディレクトリ
battle_work_dir = work_path + '/' + basename + '/match' + str(match_num)
os.makedirs(battle_work_dir, exist_ok=True)

battle_write_log_path = battle_work_dir+'/create_match_clip.log'

# ストリームハンドラの設定
stream_handler = StreamHandler()
stream_handler.setLevel(INFO)
stream_handler.setFormatter(Formatter("%(message)s"))

# ファイルハンドラの設定
file_handler = FileHandler(filename=battle_write_log_path)
file_handler.setLevel(DEBUG)
file_handler.setFormatter(
    Formatter("%(asctime)s@ %(name)s [%(levelname)s] %(funcName)s: %(message)s")
)

# ルートロガーの設定
logging.basicConfig(level=NOTSET, handlers=[stream_handler, file_handler])

logger = logging.getLogger(__name__)

# csvファイルの定義
cut_time_battle_csv = ocr_path + '/' + basename+ '/' + 'cut_time_battle.csv'

# src_movie = 'src_movie/sample.mkv'
# 切り出し秒数
cut_duration_normal = 10
cut_duration_battle = 30
cut_duration_landing = 60
# マップ表示の抽出時間
cut_duration_map= 6
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

logger.info("apex-create-movie-each.py with option: %s",(args))

scenedef=['result','memberlist','deathprotection','other','enemy','death','map']

battle_write_log_path = battle_work_dir+'/create_match_clip.log'
with open(battle_write_log_path, mode='w') as logfile:
    sss = []
    scene = []
    match = []

    logger.debug("start program, match= %s",(match_num))

    is_csv_file = os.path.isfile(cut_time_battle_csv)
    if is_csv_file:
        if os.path.getsize(cut_time_battle_csv) != 0:

            logger.debug("Open csv file")

            with open(cut_time_battle_csv) as f:
                reader = csv.reader(f)
                for row in reader:
                    sss.append(row[0])
                    scene.append(row[1])
                    match.append(row[2])
            logger.debug("Finish load csv file")
            # start = sss[0]
            start = -1
            end = sss[0]
            current = 0
            logger.debug("Start csv loop. len(sss) = %s",(len(sss)))

            for i in tqdm(range(len(sss))):

                logger.debug("  loop %s of %s" % (i, len(sss)))

                if int(match[i]) == match_num:

                    # 録画に含めたいシーンを指定[> 0:result / 1:memberlist / 2:deathprotection / 3:other / 4:enemy / 5:death / 8:kill / 9:champion
                    if int(scene[i]) == 1 or int(scene[i]) == 2 or int(scene[i]) == 4 or int(scene[i]) == 8 or int(scene[i]) == 5 or int(scene[i]) == 0 or int(scene[i]) == 3 or int(scene[i]) == 9 or int(scene[i]) == 10 or int(scene[i]) == 12 or int(scene[i]) == 13 or int(scene[i]) == 14:
                        logger.debug("    Match target scene; i = %s, sec = %s, scene = %s" % (i,sss[i], scene[i]))

                        # matchの最初(start=-1)は、scene=0をスキップする
                        if start == -1 and int(scene[i]) == 0:
                            logger.debug("    Skip result scene (lobby) ; i = %s, sec = %s, scene = %s" % (i,sss[i], scene[i]))
                            # do nothing
                        else:
                            # currentが先に進んでいる場合はスキップ
                            if float(current) <= float(sss[i]):
                                start=float(sss[i])
                                logger.debug("    check %s'th record, start = %s, current = %s, i = %s, sec = %s, scene = %s" % (i,start, current, i,sss[i], scene[i]))

                                ss = sss[i]
                                # start, endの更新処理
                                
                                #############
                                # endの更新
                                #############
                                j=i+1
                                end_flg=True
                                this_scene_list=[int(scene[i])]
                                current_time=sss[j]
                                before_time=sss[i]
                                is_keep_this_loop=False
                                logger.debug("      start j loop, sss[%s] = %s, current_time = %s, before_time = %s, end_flg = %s" % (j, sss[j], current_time, before_time, end_flg))
                                while len(sss) > j and (end_flg or float(current_time) == float(sss[j])):
                                    logger.debug("        sss[%s] = %s, current_time = %s, before_time = %s, end_flg = %s" % (j, sss[j], current_time, before_time, end_flg))
                                    if float(current_time) != float(sss[j]):
                                        before_time = current_time
                                        current_time = sss[j]

                                    # 特徴点が連続している場合
                                    if int(scene[j]) == 1 or int(scene[j]) == 2 or int(scene[j]) == 4 or int(scene[j]) == 8 or int(scene[j]) == 5 or int(scene[j]) == 3 or int(scene[j]) == 9 or int(scene[j]) == 10 or int(scene[j]) == 12 or int(scene[j]) == 13 or int(scene[j]) == 14:
                                        this_scene_list.append(int(scene[j]))
                                        # 特徴点が戦闘の場合
                                        if int(scene[j]) == 2 or int(scene[j]) == 4 or int(scene[j]) == 8 or int(scene[j]) == 12:
                                            # 次の特徴点までの時間がcut_duration_battle秒以上空く場合
                                            if float(sss[j]) - float(before_time) > float(cut_duration_battle):
                                                end = float(before_time)
                                                end_flg = False
                                                logger.debug("            set end_flg to False, [float(sss[j]) - float(before_time) > cut_duration_battle => %s - %s > %s ] j = %s, end_flg = %s, end = %s, sss[j] = %s, current_time = %s, is_keep_this_loop = %s" % (sss[j],before_time, cut_duration_battle, j, end_flg, end, sss[j], current_time, is_keep_this_loop))
                                            else:
                                                logger.debug("            keep end_flg as True, [float(sss[j]) - float(before_time) > cut_duration_battle => %s - %s > %s ] j = %s, end_flg = %s, end = %s, sss[j] = %s, current_time = %s, is_keep_this_loop = %s" % (sss[j],before_time, cut_duration_battle, j, end_flg, end, sss[j], current_time, is_keep_this_loop))                                               
                                        # 特徴点がリザルト画面、部隊全滅、チャンピョンの場合
                                        elif int(scene[j]) == 0 or int(scene[j]) == 5 or int(scene[j]) == 9:
                                            # 次の特徴点までの時間がcut_duration_result(15)秒以上空く場合
                                            if float(sss[j]) - float(before_time) > float(cut_duration_result):
                                                end = float(before_time)
                                                end_flg = False
                                                logger.debug("            set end_flg to False, [float(sss[j]) - float(before_time) > cut_duration_result => %s - %s > %s ] j = %s, end_flg = %s, end = %s, sss[j] = %s, current_time = %s, is_keep_this_loop = %s" % (sss[j],before_time, cut_duration_result, j, end_flg, end, sss[j], current_time, is_keep_this_loop))
                                            else:
                                                logger.debug("            keep end_flg as True, [float(sss[j]) - float(before_time) > cut_duration_result => %s - %s > %s ] j = %s, end_flg = %s, end = %s, sss[j] = %s, current_time = %s, is_keep_this_loop = %s" % (sss[j],before_time, cut_duration_result, j, end_flg, end, sss[j], current_time, is_keep_this_loop))
                                        # 特徴点がマップの場合
                                        elif int(scene[j]) == 10:
                                            # 次の特徴点までの時間がcut_duration_map(3)秒以上空く場合
                                            if float(sss[j]) - float(before_time) > float(cut_duration_map):
                                                end = float(before_time)
                                                end_flg = False
                                                logger.debug("            set end_flg to False, [float(sss[j]) - float(before_time) > cut_duration_map => %s - %s > %s ] j = %s, end_flg = %s, end = %s, sss[j] = %s, current_time = %s, is_keep_this_loop = %s" % (sss[j],before_time, cut_duration_map, j, end_flg, end, sss[j], current_time, is_keep_this_loop))
                                            else:
                                                logger.debug("            keep end_flg as True, [float(sss[j]) - float(before_time) > cut_duration_map => %s - %s > %s ] j = %s, end_flg = %s, end = %s, sss[j] = %s, current_time = %s, is_keep_this_loop = %s" % (sss[j],before_time, cut_duration_map, j, end_flg, end, sss[j], current_time, is_keep_this_loop))
                                        # 特徴点が降下中の場合
                                        elif int(scene[j]) == 13 or int(scene[j]) == 14:
                                            # 次の特徴点までの時間がcut_duration_battle秒以上空く場合
                                            if float(sss[j]) - float(before_time) > float(cut_duration_landing):
                                                end = float(before_time)
                                                end_flg = False
                                                logger.debug("            set end_flg to False, [float(sss[j]) - float(before_time) > cut_duration_battle => %s - %s > %s ] j = %s, end_flg = %s, end = %s, sss[j] = %s, current_time = %s, is_keep_this_loop = %s" % (sss[j],before_time, cut_duration_battle, j, end_flg, end, sss[j], current_time, is_keep_this_loop))
                                            else:
                                                logger.debug("            keep end_flg as True, [float(sss[j]) - float(before_time) > cut_duration_battle => %s - %s > %s ] j = %s, end_flg = %s, end = %s, sss[j] = %s, current_time = %s, is_keep_this_loop = %s" % (sss[j],before_time, cut_duration_battle, j, end_flg, end, sss[j], current_time, is_keep_this_loop))                                               
                                        # 特徴点がその他の場合
                                        elif int(scene[j]) == 1 or int(scene[j]) == 3:
                                            # 次の特徴点までの時間がcut_duration_normal(5)秒以上空く場合
                                            if float(sss[j]) - float(before_time) > float(cut_duration_normal):
                                                end = float(before_time)
                                                end_flg = False
                                                logger.debug("            set end_flg to False, [float(sss[j]) - float(before_time) > cut_duration_normal => %s - %s > %s ] j = %s, end_flg = %s, end = %s, sss[j] = %s, current_time = %s, is_keep_this_loop = %s" % (sss[j],before_time, cut_duration_normal, j, end_flg, end, sss[j], current_time, is_keep_this_loop))
                                            else:
                                                logger.debug("            keep end_flg as True, [float(sss[j]) - float(before_time) > cut_duration_normal => %s - %s > %s ] j = %s, end_flg = %s, end = %s, sss[j] = %s, current_time = %s, is_keep_this_loop = %s" % (sss[j],before_time, cut_duration_normal, j, end_flg, end, sss[j], current_time, is_keep_this_loop))
                                    else:
                                        end = float(before_time)
                                        end_flg=False

                                    if len(sss) > j+1 and float(sss[j]) == float(sss[j+1]):
                                        end_flg=True
                                        logger.debug("          Keep this j loop(next scene is same second): sss[%s] = %s, sss[%s+1] = %s" % (j, sss[j], j, sss[j+1]))

                                    if len(sss) - j == 1:
                                        end = float(before_time)
                                        end_flg=False

                                    if not end_flg:
                                        logger.debug("          Finished loop: end = %s, sss[%s-1] = %s, sss[%s] = %s, end_flg = %s" % (end, j, sss[j-1], j, sss[j], end_flg))
                                    else:
                                        logger.debug("          Continue to next loop: end = %s, sss[%s-1] = %s, sss[%s] = %s, end_flg = %s" % (end, j, sss[j-1], j, sss[j], end_flg))

                                    j+=1
                                    

                                # # 特徴点が戦闘の場合
                                # if int(scene[i]) == 2 or int(scene[i]) == 4 or int(scene[i]) == 8 or int(scene[i]) == 12:
                                #     j=i+1
                                #     # csvファイルで、戦闘の特徴点が継続しているところまでを抽出
                                #     while len(sss) > j and (int(scene[j]) == 2 or int(scene[j]) == 4 or int(scene[j]) == 8 or int(scene[j]) == 12):
                                #         end = float(sss[j]) + float(cut_duration_battle)
                                #         j+=1
                                # # 特徴点がリザルト画面、部隊全滅、チャンピョンの場合
                                # elif int(scene[i]) == 0 or int(scene[i]) == 5 or int(scene[i]) == 9:
                                #     j=i+1
                                #     # csvファイルで、戦闘の特徴点が継続しているところまでを抽出
                                #     while len(sss) > j and (int(scene[j]) == 0 or int(scene[j]) == 5 or int(scene[j]) == 9):
                                #         end = float(sss[j]) + float(cut_duration_result)
                                #         j+=1
                                # # 特徴点がマップの場合
                                # elif int(scene[i]) == 10:
                                #     j=i+1
                                #     # csvファイルで、戦闘の特徴点が継続しているところまでを抽出
                                #     while len(sss) > j and (int(scene[j]) == 10):
                                #         end = float(sss[j]) + float(cut_duration_map)
                                #         j+=1
                                # else:
                                #     end = float(end) + float(cut_duration_battle)

                                # クリップの時間durationを計算し、startを調整
                                # this_scene_listに入っているscene番号でduration_before,duration_afterを決定

                                # 頻度の低いイベントから判定していく
                                # マッチ開始の場合
                                if 14 in this_scene_list:
                                    duration_before = 3
                                    duration_after = float(cut_duration_landing)
                                    logger.debug("        (%s scene) duration_before = %s, duration_after = %s" % (scene_list[int(scene[i])],duration_before,duration_after))
                                # 全滅かチャンピョンの場合のみ、battle_final_recを利用.
                                elif 5 in this_scene_list or 9 in this_scene_list or 0 in this_scene_list:
                                    duration_before = battle_final_rec
                                    duration_after = death_after_sec
                                    logger.debug("        (%s scene) duration_before = %s, duration_after = %s" % (scene_list[int(scene[i])],duration_before,duration_after))
                                # landing
                                elif 13 in this_scene_list:
                                    duration_before = float(cut_duration_landing)
                                    duration_after = float(cut_duration_landing)
                                    logger.debug("        (%s scene) duration_before = %s, duration_after = %s" % (scene_list[int(scene[i])],duration_before,duration_after))
                                # battle
                                elif 4 in this_scene_list:
                                    duration_before = 3
                                    duration_after = battle_min_rec
                                    logger.debug("        (%s scene) duration_before = %s, duration_after = %s" % (scene_list[int(scene[i])],duration_before,duration_after))
                                # other
                                elif 3 in this_scene_list:
                                    duration_before = 3
                                    duration_after = 10
                                    logger.debug("        (%s scene) duration_before = %s, duration_after = %s" % (scene_list[int(scene[i])],duration_before,duration_after))
                                elif 10 in this_scene_list:
                                    duration_before = (float(cut_duration_map))/2.0
                                    duration_after = (float(cut_duration_map))/2.0
                                    logger.debug("        (%s scene) duration_before = %s, duration_after = %s" % (scene_list[int(scene[i])],duration_before,duration_after))
                                else:
                                    duration_before = 3
                                    duration_after = 10
                                    logger.debug("        (%s scene) duration_before = %s, duration_after = %s" % (scene_list[int(scene[i])],duration_before,duration_after))
                                
                                logger.debug("      Finish calc duration: start = %s,  end = %s, duration_before = %s, duration_after = %s" % (start, end,duration_before, duration_after))
                                logger.debug("      Start calc start/end/duration")


                                start = float(sss[i]) - float(duration_before)
                                logger.debug("        start = float(sss[i]) - float(duration_before) => %s = %s - %s" % (start, float(sss[i]),float(duration_before)))
                                if (float(start) < float(current)):
                                    start = current
                                end += duration_after

                                duration = float(end) - float(start)
                                current = float(end)
                                logger.debug("      Finish calc start/end/duration: start = %s,  end = %s, duration = %s" % (start, end, duration))

                                # duration = duration_before + duration_after
                                # if (float(end) - duration) < float(current):
                                #     start = current
                                #     duration = float(end) - current + float(duration_after)
                                # else:
                                #     start = float(end) - float(duration)
                                # end = start + duration
                                # current = float(end)

                                # # endを固定し、durationからstartを計算。ただし、前後のクリップで同じ時間を抽出しないように、current以前の時間をクリップしないように調整
                                # start = float(end) - float(duration) - before_scene_sec
                                # if float(current) > float(start):
                                #     duration = float(duration) - ( float(current) - float(start) )
                                #     start = current
                                # current = float(start) + float(duration)

                                # durationが0以上の場合にクリップ生成処理
                                if duration != 0:
                                    logger.info("      Export %s scene %d from %f sec for %f sec from %s" % (scene_list[int(scene[i])],i,start,duration,src_movie))

                                    match_dir = battle_work_dir + '/rec'
                                    # os.makedirs(match_dir, exist_ok=True)
                                    os.makedirs(match_dir, exist_ok=True)
                                    
                                    # if args.debug:
                                    #     duration=5
                                    #     log = "    rec duration: %f " % (duration)
                                    #     print(log)
                                    #     logfile.write(log+'\n')

                                    if args.audio:
                                        command = "ffmpeg -y -ss %s -i \"%s\" -t %d -map 0:v:0 -vcodec libx264 -map 0:a:%s -acodec copy -vsync 1 -async 1000 -loglevel quiet \"%s/%s_battle%03d_%03dm%02ds-%03dm%02ds.mp4\" </dev/null 2>&1 </dev/null 2>&1" % (start, src_movie, duration, args.audio , match_dir, basename, i, int(float(start)) // 60, int(int(float(start)) % 60) ,int(float(start)+float(duration)) // 60, int(float(start)+float(duration)) % 60)
                                    else:
                                        command = "ffmpeg -y -ss %s -i \"%s\" -t %d -map 0:v:0 -vcodec libx264 -map 0:a:1 -map 0:a:2 -map 0:a:3 -vsync 1 -async 1000 -loglevel quiet \"%s/%s_battle%03d_%03dm%02ds-%03dm%02ds.mp4\" </dev/null 2>&1 </dev/null 2>&1" % (start, src_movie, duration, match_dir, basename, i, int(float(start)) // 60, int(int(float(start)) % 60) ,int(float(start)+float(duration)) // 60, int(float(start)+float(duration)) % 60)

                                    logger.debug("      ffmpeg command: %s" % (command))
                                    # subprocess.run(command, shell=True)
                                    subprocess.run(command, shell=True,stdout = subprocess.DEVNULL,stderr = subprocess.DEVNULL)
                                    subprocess.run('ls -al '+match_dir, shell=True,stdout = subprocess.DEVNULL,stderr = subprocess.DEVNULL)
                                else:
                                    logger.debug("      Skip export clip in loop: %s" % (i))

                                if int(scene[i]) == 5 or int(scene[i]) == 0 or int(scene[i]) == 9 or int(scene[i]) == 8:
                                    start = -1
                                else:
                                    start = float(ss)
                                # end = ss
                                # else:
                                #     end = ss
                                #     if start == -1 and not ( int(scene[i]) == 5 or int(scene[i]) == 0 or int(scene[i]) == 9 or int(scene[i]) == 8):
                                #         start = float(ss)
                                #log = "  ss:%s start:%s end:%s scene:%s" % (ss, start, end, scene[i])
                                #print(log)
                                #logfile.write(log+'\n')
                            else:
                                logger.debug("    Skip %s'th record (current is ahead of start), current = %s, i = %s, sec = %s, scene = %s" % (i,current, i,sss[i], scene[i]))
                else:
                    logger.debug("    Skip scene (the number 'match' is unmatch); i = %s, sec = %s, scene = %s" % (i,sss[i], scene[i]))

            # # csvファイルを一通り捜査した後の録画処理
            # if not start == -1:
            #     end = float(end) + float(cut_duration_battle)
            #     duration = max(float(end) - float(start) + before_scene_sec, battle_min_rec)
            #     log = "Export battle scene %d from %.2f sec for %.2f sec from %s" % (int(i),float(start),float(duration),src_movie)
            #     print(log)
            #     match_dir = battle_work_dir + '/rec'
            #     os.makedirs(match_dir, exist_ok=True)
            #     # os.makedirs('/rec', exist_ok=True)
            #     logfile.write(log+'\n')

            #     if args.debug:
            #         duration=5
            #         log = "  rec duration: %f " % (duration)
            #         print(log)
            #         logfile.write(log+'\n')

            #     if args.audio:
            #         command = "ffmpeg -y -ss %s -i \"%s\" -t %d -map 0:v:0 -vcodec libx264 -map 0:a:%s -acodec copy -vsync 1 -async 1000 \"%s/%s_battle%03d_%03dm%02ds-%03dm%02ds.mp4\" </dev/null 2>&1" % (start, src_movie, duration, args.audio ,match_dir, basename, i, int(float(start)) // 60, int(int(float(start)) % 60) ,int(float(start)+float(duration)) // 60, int(float(start)+float(duration)) % 60)
            #     else:
            #         command = "ffmpeg -y -ss %s -i \"%s\" -t %d -map 0:v:0 -vcodec libx264 -map 0:a:1 -map 0:a:2 -map 0:a:3 -vsync 1 -async 1000 \"%s/%s_battle%03d_%03dm%02ds-%03dm%02ds.mp4\" </dev/null 2>&1" % (start, src_movie, duration, match_dir, basename, i, int(float(start)) // 60, int(int(float(start)) % 60) ,int(float(start)+float(duration)) // 60, int(float(start)+float(duration)) % 60)
            #     log = "  ffmpeg command: %s" % (command)
            #     print(log)
            #     logfile.write(log+'\n')
            #     subprocess.run(command, shell=True)
            #     subprocess.run('ls -al '+match_dir, shell=True,stdout = subprocess.DEVNULL,stderr = subprocess.DEVNULL)

            # subprocess.run('ls -al '+match_dir, shell=True,stdout = subprocess.DEVNULL,stderr = subprocess.DEVNULL)
            # #shutil.move('/rec', match_dir)

    logfile.close


