#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image
import sys
import cv2
import csv
import os
import re
import pathlib
from tqdm import tqdm
import numpy as np
# from logging import StreamHandler, Formatter, INFO, getLogger
import logging
import pandas as pd
import pyocr
import pyocr.builders
import argparse


# def init_logger.info():
#     handler = StreamHandler()
#     handler.setLevel(INFO)
#     handler.setFormatter(Formatter("[%(asctime)s] [%(threadName)s] %(message)s"))
#     logger = getLogger()
#     logger.addHandler(handler)
#     logger.setLevel(INFO)

def pil2cv(imgPIL):
    imgCV_RGB = np.array(imgPIL, dtype=np.uint8)
    imgCV_BGR = np.array(imgPIL)[:, :, ::-1] # H方向とW方向はそのままに、RGBを逆順にする
    return imgCV_BGR

def change_flg(name,flg,change_bool,bool):
    ret_flg = change_bool
    if flg ^ bool:
        logger.warning("Switch flg %s from %s to %s" % (name, flg, bool))
        ret_flg = True
    return bool, ret_flg

def tail_pd(fn, n):
    df = pd.read_csv(fn)
    return df.tail(n).values.tolist()

def apex_ocr(img, cnt,fps, type='debug',threshold_flg=False, threshold_val=[169,169,169], crop_flg=False ,crop_loc=(0,0,0,0), debug_dir='/result'):
    # if args.debug:
    #     logger.info('apex_ocr')
    img_org = Image.fromarray(pil2cv(img))

    if threshold_flg:
        img_rgb = img_org.convert("RGB")
        pixels = img_rgb.load()
        # 色相反転＆2諧調化
        r_max = threshold_val[0]
        g_max = threshold_val[1]
        b_max = threshold_val[2]
        for j in range(img_rgb.size[1]):
            for i in range(img_rgb.size[0]):
                pixels[i,j] = (255 - pixels[i, j][0], 255 - pixels[i, j][1], 255- pixels[i, j][2])
                if (pixels[i, j][0] > r_max or pixels[i, j][1] > g_max or pixels[i, j][2] > b_max):
                    pixels[i, j] = (255, 255, 255)
                else:
                    pixels[i, j] = (0, 0, 0)
        image = img_rgb
    else:
        image = img_org
     
    # 番号の部分を切り抜き
    if crop_flg:
        img_box = image.crop(crop_loc)
        image = img_box

    if args.debug:
        # 画像のファイル出力
        out_path_image = os.path.join(
            debug_dir, "%s_frame%d.%02d.jpg" % (type, cnt/fps, 100 * (cnt % fps)/fps))
        image.save(out_path_image)

    try:
        txt = tool.image_to_string(
            image,
            lang=lang,
            builder=pyocr.builders.TextBuilder(tesseract_layout=3)
        )
    except Exception as e:
        print(e)
        txt=''

    txt = re.sub('([あ-んア-ン一-龥ー])\s+((?=[あ-んア-ン一-龥ー]))',
        r'\1\2', txt)
    return txt

def apex_search(txt, type, search_text, cnt, status_dict, fps,writer,match,battle_dir, search_text_exception=[]):
    ret_no_start = 0
    if args.debug:
        # デバッグ：OCR結果のテキストを出力
        out_path_txt = os.path.join(
            battle_dir, "%s_frame%d.%02d.txt" % (type, cnt/fps, 100 * (cnt % fps)/fps))
        with open(out_path_txt, mode='w') as f:
            f.write(txt)

    except_search_flg = False
    ret_result = False
    if txt.find(search_text) != -1:
        if search_text_exception:
            for except_txt in search_text_exception:
                if txt.find(except_txt) != -1:
                    except_search_flg = True
        if not except_search_flg:
            writer.writerow(["%d.%02d" % (cnt/fps, 100 * (cnt % fps)/fps),status_dict,match])
            # シーン判定をしばらく止める
            ret_no_start = int(fps * skip_after_scan)
            ret_result = True
            if args.debug:
                logger.info("[%4.1f]  in apex search: find text %s (status: %s) [%s, match %s]" % (cnt/fps, search_text, status_dict, basename, match))
    return ret_result, ret_no_start

def main():
    # 保存インデックス
    save_index = 0

    # 動画を読み込む
    cap = cv2.VideoCapture(src_movie)
    if not cap.isOpened():
        logger.warning('cv2 exception error')
        sys.exit(1)
    # フレーム数を取得
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    logger.warning("frame count: %s" % frame_count)
    # 1秒あたりフレーム数を取得
    fps = cap.get(cv2.CAP_PROP_FPS)
    # logger.info("fps: %s" % fps)
    logger.warning("fps: %s" % fps)
    # 1秒に1回予測する
    skip = int(fps/4)
    # フレーム
    i = 0
    no_start = 0
    match = 1
    # 切り出し開始しないカウントダウン
    
    if args.skip is None:
        is_csv_file = os.path.isfile(cut_time_battle_csv)
        if is_csv_file:
            if os.path.getsize(cut_time_battle_csv) != 0:
                last_ocr=tail_pd(cut_time_battle_csv,1)
                no_start=int(last_ocr[0][0]) * fps
                match=int(last_ocr[0][2])
        else:
            no_start = 0
            match = 1
    else:
        no_start=args.skip

    logger.warning("init no_start / match: %d / %d" % (no_start, match))

    last_time_battle = 0

    flg_in_lobby = False
    flg_in_battle = False
    flg_in_result = False

    flg_smooth = True

    # 書き出しCSVファイル
    for i in tqdm(range(frame_count)):
        # ディレクトリの準備
        # matchディレクトリ
        match_dir = base_dir + '/match' + str(match)
        # battleディレクトリ
        battle_dir = match_dir + '/battle'
        # debugディレクトリ
        debug_dir = match_dir + '/debug'
        # resultディレクトリ
        result_dir = match_dir + '/result'
        os.makedirs(battle_dir, exist_ok=True)
        os.makedirs(result_dir, exist_ok=True)
        os.makedirs(debug_dir, exist_ok=True)
        logger.debug("before read")

        # match_dir に、flg_in_progress_matchファイルを作成する
        flg_in_progress_match = os.path.join(match_dir, 'flg_in_progress_match')
        pathlib.Path(flg_in_progress_match).touch()

        ret, frame = cap.read()
        # logger.info("frame : %s" % frame)
        if ret:
            # if ( i >= 3251*fps and i % skip == 0 and no_start == 0 ) or not flg_smooth:
            if i % skip == 0 and ( int(no_start) == 0 or not flg_smooth):
                with open(cut_time_battle_csv, 'a') as f:
                    writer = csv.writer(f)
                    img = cv2.resize(frame, (1920, 1080))
                    flg_change_lobby = False
                    flg_change_result = False
                    flg_change_battle = False
                    if args.debug:
                      txt = apex_ocr(img, i,fps, 'debug',False, [169,169,169], False, (0, 0, 1920, 1080),debug_dir)  

                    ####################################                    
                    # 画面右上通知領域のOCR
                    ####################################
                    txt = apex_ocr(img,i,fps, 'top_right',False, [169,169,169], True, (1290, 173, 1800, 400),debug_dir)
                    result_a,this_no_start = apex_search(txt, 'enemy', '発見', i , '4',fps,writer,match,debug_dir)
                    result_b,this_no_start = apex_search(txt, 'map', 'クラフト', i , '6',fps,writer,match,debug_dir)
                    result_c,this_no_start = apex_search(txt, 'result', '部隊の合計キル', i , '0',fps,writer,match,debug_dir)
                    result_d,this_no_start = apex_search(txt, 'enemy', '敵の', i , '4',fps,writer,match,debug_dir)
                    result_e,this_no_start = apex_search(txt, 'enemy', 'シールドが', i , '4',fps,writer,match,debug_dir)
                    result_f,this_no_start = apex_search(txt, 'enemy', 'が割れた', i , '4',fps,writer,match,debug_dir)
                    result_g,this_no_start = apex_search(txt, 'enemy', '近くに', i , '4',fps,writer,match,debug_dir)
                    result_h,this_no_start = apex_search(txt, 'enemy', 'に部隊', i , '4',fps,writer,match,debug_dir)
                    result_i,this_no_start = apex_search(txt, 'enemy', '着地', i , '4',fps,writer,match,debug_dir)
                    result = result_a or result_b or result_d or result_e or result_f or result_g or result_h or result_i
                    if result:
                        no_start = max(int(fps * skip_after_scan), no_start)
                        flg_in_lobby ,flg_change_lobby = change_flg('lobby',flg_in_lobby,flg_change_lobby,False)
                    # 敵を発見(ping)
                    if result_a:
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,True)
                        last_time_battle = i
                        out_path_image = os.path.join(
                            battle_dir, "enemy_found_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Found enemy [%s, match %s]" % (i/fps,basename, match))
                    # 敵のシールドが割れた
                    if result_d or result_e or result_f:
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,True)
                        out_path_image = os.path.join(
                            battle_dir, "enemy_attack_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Break enemy shield [%s, match %s]" % (i/fps,basename, match))
                    # 敵が近くに着地
                    if result_g or result_h or result_i:
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,True)
                        last_time_battle = i
                        out_path_image = os.path.join(
                            battle_dir, "enemy_landing_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Enemy landed at near spot [%s, match %s]" % (i/fps,basename, match))
                    # マップ画面
                    if result_b:
                        logger.info("[%4.1f]Open map [%s, match %s]" % (i/fps,basename, match))
                        out_path_image = os.path.join(
                            result_dir, "map_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        flg_in_lobby ,flg_change_lobby = change_flg('lobby',flg_in_lobby,flg_change_lobby,False)
                    # リザルト画面
                    if result_c:
                        out_path_image = os.path.join(
                            result_dir, "result_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        # flg_in_lobbyがFalse -> True遷移する際にmatchをインクリメント
                        logger.info("[%4.1f]Show result [%s, match %s]" % (i/fps,basename, match))
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,False)
                        flg_in_lobby ,flg_change_lobby = change_flg('lobby',flg_in_lobby,flg_change_lobby,False)
                        flg_in_result ,flg_change_result = change_flg('result',flg_in_result,flg_change_result,True)
                        last_time_battle = 0

                        # ログに"nock"の文字がある場合（kill/downログを想定）
                        if flg_in_battle: # 降下中に譲渡される場合を除外するため，flg_in_battleをand条件として設定
                            result_d,this_no_start = apex_search(txt, 'kdown', 'nock', i , '4',fps,writer,match,debug_dir,['撃破','ありがとう'])
                            if result_d:
                                out_path_image = os.path.join(
                                    battle_dir, "kd_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                                cv2.imwrite(out_path_image,img)
                                logger.info("[%4.1f]Knock down [%s, match %s]" % (i/fps,basename, match))
                                flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,True)
                                flg_in_lobby ,flg_change_lobby = change_flg('lobby',flg_in_lobby,flg_change_lobby,False)
                                flg_in_result ,flg_change_result = change_flg('result',flg_in_result,flg_change_result,False)

                    ####################################                    
                    # 部隊全滅の中央領域
                    ####################################　ore
                    # 部隊全滅（in game）
                    txt = apex_ocr(img,i,fps, 'center',False, [169,169,169], True, (842, 373, 1070, 448),debug_dir)
                    result_a,this_no_start = apex_search(txt, 'death', '部隊', i , '5',fps,writer,match,debug_dir)
                    result_b,this_no_start = apex_search(txt, 'champion', 'アリーナ', i , '5',fps,writer,match,debug_dir)
                    result_c,this_no_start = apex_search(txt, 'champion', 'チャンピオン', i , '5',fps,writer,match,debug_dir)
                    result_d,this_no_start = apex_search(txt, 'lobby', '戦績を表示', i , '7',fps,writer,match,debug_dir)
                    if result_a:
                        out_path_image = os.path.join(
                            battle_dir, "death_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,False)
                        logger.info("[%4.1f]Eliminated squad [%s, match %s]" % (i/fps,basename, match))
                    if result_b or result_c:
                        out_path_image = os.path.join(
                            battle_dir, "champion_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,False)
                        flg_in_lobby ,flg_change_lobby = change_flg('lobby',flg_in_lobby,flg_change_lobby,False)
                        flg_in_result ,flg_change_result = change_flg('result',flg_in_result,flg_change_result,True)
                        logger.info("Arena Champion result [%s, match %s]" % (basename, match))
                    # ロビー画面に戻る
                    if result_d:
                        logger.info("In lobby [%s, match %s]" % (basename, match))
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,False)
                        flg_in_lobby ,flg_change_lobby = change_flg('lobby',flg_in_lobby,flg_change_lobby,True)
                        flg_in_result ,flg_change_result = change_flg('result',flg_in_result,flg_change_result,False)

                    ####################################                    
                    # 撃破表示
                    ####################################
                    txt = apex_ocr(img,i,fps, 'kill_display',False, [169,169,169], True, (670, 750, 1328, 810),debug_dir)
                    result_a,this_no_start = apex_search(txt, 'kill', '撃破', i , '8',fps,writer,match,debug_dir)
                    result_b,this_no_start = apex_search(txt, 'kill', 'アシスト', i , '8',fps,writer,match,debug_dir)
                    # 敵を撃破
                    if result_a or result_b:
                        out_path_image = os.path.join(
                            battle_dir, "kill_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Kill enemy [%s, match %s]" % (i/fps,basename, match))

                    ####################################                    
                    # 字幕＋画面中央
                    ####################################
                    txt = apex_ocr(img,i,fps, 'subtitle',False, [169,169,169], True, (500, 810, 1406, 930),debug_dir)
                    result_a,this_no_start = apex_search(txt, 'kdown', 'ノックダウン', i , '4',fps,writer,match,debug_dir)
                    result_c,this_no_start = apex_search(txt, 'kill', '自己復活', i , '8',fps,writer,match,debug_dir)
                    result_d,this_no_start = apex_search(txt, 'other', 'ホールド', i , '3',fps,writer,match,debug_dir)
                    result_e,this_no_start = apex_search(txt, 'other', '同行', i , '3',fps,writer,match,debug_dir)
                    result_f,this_no_start = apex_search(txt, 'other', 'ジャンプ', i , '3',fps,writer,match,debug_dir)
                    result_g,this_no_start = apex_search(txt, 'champion', 'なりました', i , '5',fps,writer,match,debug_dir)
                    result_h,this_no_start = apex_search(txt, 'kill', 'をノックダウン', i , '4',fps,writer,match,debug_dir)
                    result_i,this_no_start = apex_search(txt, 'kill', 'ダメージ', i , '4',fps,writer,match,debug_dir)
                    result_j,this_no_start = apex_search(txt, 'blackhole', '重力の', i , '4',fps,writer,match,debug_dir)
                    result_k,this_no_start = apex_search(txt, 'blackhole', '特異点', i , '4',fps,writer,match,debug_dir)
                    result_l,this_no_start = apex_search(txt, 'enemy', 'フーリガンども', i , '4',fps,writer,match,debug_dir) # 味方被弾(ホライゾン)
                    result_l,this_no_start = apex_search(txt, 'enemy', '撃たれて', i , '4',fps,writer,match,debug_dir) # 味方被弾(オクタン/ホライゾン/シア)
                    result_m,this_no_start = apex_search(txt, 'enemy', '攻撃されている', i , '4',fps,writer,match,debug_dir) # レブナント/クリプト被弾
                    result_m,this_no_start = apex_search(txt, 'enemy', '攻撃がきた', i , '4',fps,writer,match,debug_dir) # ミラージュ被弾
                    result_n,this_no_start = apex_search(txt, 'enemy', 'ダウンした', i , '4',fps,writer,match,debug_dir) # ヒューズダウン
                    result_n,this_no_start = apex_search(txt, 'enemy', '雑魚に', i , '4',fps,writer,match,debug_dir) # ヒューズ被弾
                    result_n,this_no_start = apex_search(txt, 'enemy', 'ダウンさせられた', i , '4',fps,writer,match,debug_dir) # ヒューズダウン
                    result_o,this_no_start = apex_search(txt, 'enemy', 'ダメージをくれて', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(ホライゾン)
                    result_p,this_no_start = apex_search(txt, 'enemy', '命中', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(クリプト)
                    result_q,this_no_start = apex_search(txt, 'enemy', '撃ってる', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(ホライゾン/ヒューズ)
                    result_r,this_no_start = apex_search(txt, 'enemy', '撃っている', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(ホライゾン)
                    result_s,this_no_start = apex_search(txt, 'enemy', 'アタシとニュートがダウン', i , '4',fps,writer,match,debug_dir) # ホライゾンダウン
                    result_t,this_no_start = apex_search(txt, 'enemy', 'ダウンだ', i , '4',fps,writer,match,debug_dir) # ヒューズダウン
                    result_t,this_no_start = apex_search(txt, 'enemy', 'ナックルクラスター', i , '4',fps,writer,match,debug_dir) # ヒューズ戦術
                    result_u,this_no_start = apex_search(txt, 'enemy', '弾でもくらいな', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(ヒューズ)
                    result_v,this_no_start = apex_search(txt, 'enemy', '引き金を引くよ', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(ホライゾン)
                    result_v,this_no_start = apex_search(txt, 'enemy', '科学的に表現', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(ホライゾン)
                    result_v,this_no_start = apex_search(txt, 'enemy', '敵がいる', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(ホライゾン)
                    result_v,this_no_start = apex_search(txt, 'enemy', 'すぐ近くに', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(ホライゾン)
                    result_w,this_no_start = apex_search(txt, 'enemy', 'ダメージを受けている', i , '4',fps,writer,match,debug_dir) # 味方被弾(クリプト)
                    result_w,this_no_start = apex_search(txt, 'enemy', 'ベールを', i , '4',fps,writer,match,debug_dir) # 戦術(シア)
                    result_w,this_no_start = apex_search(txt, 'enemy', 'ベールの', i , '4',fps,writer,match,debug_dir) # 戦術(シア)
                    result_w,this_no_start = apex_search(txt, 'enemy', '外します', i , '4',fps,writer,match,debug_dir) # 戦術(シア)
                    result_w,this_no_start = apex_search(txt, 'enemy', 'お見せしま', i , '4',fps,writer,match,debug_dir) # 戦術(シア)
                    result_w,this_no_start = apex_search(txt, 'enemy', '攻撃中です', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(シア)
                    result_w,this_no_start = apex_search(txt, 'enemy', '射撃開始', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(シア)
                    result_w,this_no_start = apex_search(txt, 'enemy', '別部隊から', i , '4',fps,writer,match,debug_dir) # シア被弾
                    result_w,this_no_start = apex_search(txt, 'enemy', '攻撃を受けて', i , '4',fps,writer,match,debug_dir) # シア被弾
                    result_w,this_no_start = apex_search(txt, 'enemy', '攻撃されて', i , '4',fps,writer,match,debug_dir) # シア被弾
                    result_w,this_no_start = apex_search(txt, 'enemy', '敵の姿を', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(シア)
                    result_w,this_no_start = apex_search(txt, 'enemy', '敵をダウン', i , '4',fps,writer,match,debug_dir) # 敵ダウン(シア)
                    result_w,this_no_start = apex_search(txt, 'enemy', '確認できます', i , '4',fps,writer,match,debug_dir) # 敵ダメージ(シア)
                    result_w,this_no_start = apex_search(txt, 'enemy', 'ダウンしました', i , '4',fps,writer,match,debug_dir) # シアダウン
                    result_w,this_no_start = apex_search(txt, 'enemy', '私のハート', i , '4',fps,writer,match,debug_dir) # シアウルト
                    result_w,this_no_start = apex_search(txt, 'enemy', 'ハートを聞き', i , '4',fps,writer,match,debug_dir) # シアウルト
                    result_w,this_no_start = apex_search(txt, 'enemy', '美しいですね', i , '4',fps,writer,match,debug_dir) # 敵全滅(シア)
                    result_w,this_no_start = apex_search(txt, 'enemy', '美と化し', i , '4',fps,writer,match,debug_dir) # 敵全滅(シア)

                    # 戦闘状態抽出の共通処理
                    result_in_battle = result_a or result_b or result_c or result_h or result_i or result_j or result_k or result_l or result_m or result_n or result_o or result_p or result_q or result_r or result_s or result_t or result_u or result_v or result_w
                    if result_in_battle:
                        no_start = max(int(fps * skip_after_scan), no_start)
                        last_time_battle = i
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,True)
                        flg_in_lobby ,flg_change_lobby = change_flg('lobby',flg_in_lobby,flg_change_lobby,False)
                        flg_in_result ,flg_change_result = change_flg('result',flg_in_result,flg_change_result,False)

                    # ノックダウン
                    if result_a:
                        out_path_image = os.path.join(
                            battle_dir, "kd_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Knock down [%s, match %s]" % (i/fps,basename, match))
                    # 敵をノックダウン
                    if result_h or result_i:
                        out_path_image = os.path.join(
                            battle_dir, "knock_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Knock down enemy [%s, match %s]" % (i/fps,basename, match))
                    # ダウン状態（金ノックダウンシールド有）
                    if result_c:
                        out_path_image = os.path.join(
                            battle_dir, "down_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Down player [%s, match %s]" % (i/fps,basename, match))
                    # 降下中
                    if result_d or result_e or result_f:
                        out_path_image = os.path.join(
                            battle_dir, "landing_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Landing [%s, match %s]" % (i/fps,basename, match))
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,False)
                        flg_in_lobby ,flg_change_lobby = change_flg('lobby',flg_in_lobby,flg_change_lobby,False)
                    # Apex Champion
                    if result_g:
                        out_path_image = os.path.join(
                            battle_dir, "champion_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("Apex Champion [%s, match %s]" % (basename, match))
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,False)
                        flg_in_lobby ,flg_change_lobby = change_flg('lobby',flg_in_lobby,flg_change_lobby,False)
                        flg_in_result ,flg_change_result = change_flg('result',flg_in_result,flg_change_result,True)
                    # ホライゾンULT
                    if result_j or result_k:
                        out_path_image = os.path.join(
                            battle_dir, "blackhole_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Use Blackhole [%s, match %s]" % (i/fps,basename, match))
                    # 味方被弾
                    if result_l or result_m or result_w:
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,True)
                        out_path_image = os.path.join(
                            battle_dir, "enemy_member_damaged_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Attacked by enemy [%s, match %s]" % (i/fps,basename, match))
                    # 味方がダウン
                    if result_n or result_s or result_t:
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,True)
                        out_path_image = os.path.join(
                            battle_dir, "enemy_member_down_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Member down [%s, match %s]" % (i/fps,basename, match))
                    # 敵がダメージ
                    if result_o or result_p or result_q or result_r or result_u or result_v:
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,True)
                        out_path_image = os.path.join(
                            battle_dir, "enemy_attack_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        logger.info("[%4.1f]Attacking enemy [%s, match %s]" % (i/fps,basename, match))


                    ####################################                    
                    # 画面中央
                    ####################################
                    # リザルト
                    txt = apex_ocr(img,i,fps, 'result',False, [110,110,255], True, (780, 120, 1183, 184),debug_dir)
                    result_a,this_no_start = apex_search(txt, 'result', '部隊', i , '0',fps,writer,match,debug_dir)
                    result_b,this_no_start = apex_search(txt, 'result', 'マッチリザルト', i , '0',fps,writer,match,debug_dir)
                    result_c,this_no_start = apex_search(txt, 'result', '全滅', i , '0',fps,writer,match,debug_dir)
                    result_d,this_no_start = apex_search(txt, 'result', '隊全', i , '0',fps,writer,match,debug_dir)
                    result = result_a or result_b or result_c or result_d
                    if result:
                        no_start = max(int(fps * skip_after_scan), no_start)
                        out_path_image = os.path.join(
                            result_dir, "result_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)
                        flg_in_battle ,flg_change_battle = change_flg('battle',flg_in_battle,flg_change_battle,False)
                        flg_in_lobby ,flg_change_lobby = change_flg('lobby',flg_in_lobby,flg_change_lobby,False)
                        flg_in_result ,flg_change_result = change_flg('result',flg_in_result,flg_change_result,True)
                        last_time_battle = 0
                        logger.info("[%4.1f]Show result [%s, match %s]" % (i/fps,basename, match))

                    #################################
                    # 一通りのOCR終了後の処理
                    #################################

                    # no_startの設定
                    if flg_in_lobby:
                        no_start = max(fps * skip_in_lobby, no_start)
                    if not flg_in_battle:
                        no_start = max(fps * skip_in_normal, no_start)
                    if flg_in_result:
                        no_start = 0
                    if flg_in_battle and ( i - last_time_battle ) >= battle_duration * fps:
                        flg_in_battle = False
                        last_time_battle = 0
                        logger.info("[%4.1f]Finish battle [%s, match %s]" % (i/fps,basename, match))
                    if args.debug:
                        no_start = 0

                    # ロビー　→　マッチ開始の処理
                    if not flg_in_lobby and flg_change_lobby:
                        logger.info("[%4.1f][EndLoop]Start new match [nos=%d] [%s, match %s]" % (i/fps, no_start,basename, match))

                        # flg_in_progress_matchファイルを削除
                        if os.path.exists(flg_in_progress_match):
                            os.remove(flg_in_progress_match)
                        # match_dir に、ocr_finishedファイルを作成する
                        ocr_finished = os.path.join(match_dir, 'ocr_finished')
                        pathlib.Path(ocr_finished).touch()
                        
                        match += 1
                        # matchディレクトリ
                        match_dir = base_dir + '/match' + str(match)
                        # battleディレクトリ
                        battle_dir = match_dir + '/battle'
                        # debugディレクトリ
                        debug_dir = match_dir + '/debug'
                        # resultディレクトリ
                        result_dir = match_dir + '/result'
                        os.makedirs(battle_dir, exist_ok=True)
                        os.makedirs(result_dir, exist_ok=True)
                        os.makedirs(debug_dir, exist_ok=True)
                        # with open(flg_in_progress, mode='w') as f:
                        #     f.write(str(i))
                    # 戦闘終了
                    if not flg_in_battle and flg_change_battle:
                        logger.info("[%4.1f][EndLoop]Finish battle [nos=%d] [%s, match %s]" % (i/fps, no_start,basename, match))

                    # リザルト
                    if flg_in_result:
                        logger.info("[%4.1f][EndLoop]Result window [nos=%d] [%s, match %s]" % (i/fps, no_start,basename, match))
                        out_path_image = os.path.join(
                            result_dir, "result_%05d_%d.%02d.jpg" % (save_index,i/fps, 100 * (i % fps)/fps))
                        cv2.imwrite(out_path_image,img)

                    # リザルト→ロビー
                    if not flg_in_result and flg_change_result:
                        logger.info("[%4.1f][EndLoop]Finish showing result [nos=%d] [%s, match %s]" % (i/fps, no_start,basename, match))

                    save_index += 1
            if no_start >= 1:
                no_start -= 1
            if args.debug:
                logger.info('time:%4.1f, no_start:%d, FLG_lobby:%s, FLG_battle:%s (last: %4.1f), FPS:%.1f [%s, match %s]' % (i/fps, no_start, flg_in_lobby, flg_in_battle, (last_time_battle * fps), fps, basename, match))
        else:
            logger.warning("Skipped frame %d (read fail) [%s, match %s]" % (i,basename, match))
            # break

if __name__ == "__main__":
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
    parser.add_argument("--skip", type=int,
                        help="Skip ocr")
    parser.add_argument("--audio", type=str,
                        help="Audio Channel[Optional]")
    args = parser.parse_args()

    # 切り出し元動画パス
    src_movie = args.src
    basename = os.path.splitext(os.path.basename(src_movie))[0]
    # フレーム画像格納ディレクトリ
    dst_dir = 'src_image'
    # ファイル出力先のパスを指定
    export_path = args.output

    # tesseractの準備
    # pythonプログラムのディレクトリを確認
    p = pathlib.Path(os.path.dirname(__file__))
    program_path = str(p.resolve())
    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        print("No OCR tool found")
        sys.exit(1)
    tool = tools[0]
    lang='jpn'

    # baseディレクトリ
    base_dir = export_path + '/' + basename
    try:
        os.makedirs(base_dir, exist_ok=True)
    except FileExistsError:
        pass
    # csvファイルの定義
    cut_time_battle_csv = base_dir + '/cut_time_battle.csv'
    flg_in_progress = base_dir + '/flg_in_progress'

    logger = logging.getLogger("logger")    #logger名loggerを取得
    logger.setLevel(logging.INFO)  #標準出力のloggerとしてはINFOで

    #handler1を作成
    handler1 = logging.StreamHandler()
    handler1.setLevel(logging.WARN)     #handler2はLevel.WARN以上
    handler1.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))

    #handler2を作成
    handler2 = logging.FileHandler(filename=base_dir+"/ocr.log")  #handler2はファイル出力
    handler2.setLevel(logging.DEBUG)     #handler2はLevel.WARN以上
    handler2.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))

    #loggerに2つのハンドラを設定
    logger.addHandler(handler1)
    logger.addHandler(handler2)

    # init_logger.info()
    logger.warning("main start [%s]",(basename))


    ####################################
    # 捜査頻度設定
    ####################################
    skip_after_scan = 0
    skip_in_lobby = 4
    skip_in_normal = 2
    battle_duration = 16

    main()
