from PIL import Image
import sys
import cv2
import csv
import os
import re
import pathlib
from tqdm import tqdm
import numpy as np
from logging import StreamHandler, Formatter, INFO, getLogger
import pyocr
import pyocr.builders
import argparse
import datetime
import pytesseract

parser = argparse.ArgumentParser()
parser.add_argument("src", type=str,
                    help="Target file")
parser.add_argument("--debug", action="store_true",
                    help="Debug mode")
parser.add_argument("--flg_threshold", type=bool,default=False,
                    help="Threshold flag[Optional]")
parser.add_argument("--flg_crop", type=bool,default=False,
                    help="Crop flag[Optional]")
parser.add_argument("--audio", type=str,
                    help="Audio Channel[Optional]")
parser.add_argument('--threshold',
                      nargs='+',
                      dest='threshold',
                      type=int,
                      default=False)
parser.add_argument('--crop',
                      nargs='+',
                      dest='crop',
                      type=int,
                      default=False)
args = parser.parse_args()

def init_logger():
    handler = StreamHandler()
    handler.setLevel(INFO)
    handler.setFormatter(Formatter("[%(asctime)s] [%(threadName)s] %(message)s"))
    logger = getLogger()
    logger.addHandler(handler)
    logger.setLevel(INFO)

def pil2cv(imgPIL):
    imgCV_RGB = np.array(imgPIL, dtype=np.uint8)
    imgCV_BGR = np.array(imgPIL)[:, :, ::-1] # H方向とW方向はそのままに、RGBを逆順にする
    return imgCV_BGR

def change_flg(name,flg,bool):
    ret_flg = False
    if flg ^ bool:
        getLogger().info("Switch flg %s from %s to %s" % (name, flg, bool))
        ret_flg = True
    return bool, ret_flg

def apex_ocr(img, cnt,fps,filename, type='debug',threshold_flg=False, threshold_val=[169,169,169], crop_flg=False ,crop_loc=(0,0,0,0)):

    img_org = img

    if threshold_flg:
        print("Threshold true")
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
        print("Threshold false")
        image = img_org
     
    # 番号の部分を切り抜き
    if crop_flg:
        img_box = image.crop(crop_loc)
        image = img_box

    # out_path_image = "./result/" + os.path.basename(filename)
    # image.save(out_path_image)

    txt = tool.image_to_string(
        image,
        lang=lang,
        builder=pyocr.builders.TextBuilder(tesseract_layout=3)
    )

    txt = re.sub('([あ-んア-ン一-龥ー])\s+((?=[あ-んア-ン一-龥ー]))',
        r'\1\2', txt)
    return txt

def apex_pick_place(img, cnt,fps,filename, color_val=[230,179,63], crop_flg=False ,crop_loc=(0,0,0,0)):

    img_org = img
    threshold = 70
    color_val=[230,179,0]
    img_rgb = img_org.convert("RGB")
    pixels = img_rgb.load()
    # 色相反転＆2諧調化
    r_pick_min = float(color_val[0]) - threshold
    g_pick_min = float(color_val[1]) - threshold
    b_pick_min = float(color_val[2]) - threshold
    r_pick_max = float(color_val[0]) + threshold
    g_pick_max = float(color_val[1]) + threshold
    b_pick_max = float(color_val[2]) + threshold
    for j in range(img_rgb.size[1]):
        for i in range(img_rgb.size[0]):
            if ( r_pick_min <= pixels[i, j][0] <= r_pick_max and g_pick_min <= pixels[i, j][1] <= g_pick_max and b_pick_min <= pixels[i, j][2] <= b_pick_max):
                pixels[i, j] = (0, 0, 0)
            else:
                pixels[i, j] = (255, 255, 255)
    image = img_rgb
     
    # 番号の部分を切り抜き
    if crop_flg:
        img_box = image.crop(crop_loc)
        image = img_box

    # out_path_image = "./result/pick_" + os.path.basename(filename)
    # image.save(out_path_image)

    txt = tool.image_to_string(
        image,
        lang=lang,
        builder=pyocr.builders.TextBuilder(tesseract_layout=7)
    )

    # 仁→位
    txt = re.sub('仁',
        r'位', txt)

    # 17→位
    txt = re.sub('17$',
        r'位', txt)

    # ]→1
    txt = re.sub(']',
        r'1', txt)

    # 人7 -> 位
    txt = re.sub('人7',
        r'位', txt)

    # 人 -> 位
    txt = re.sub('人',
        r'位', txt)

    # る位 -> 3
    txt = re.sub('る位',
        r'3', txt)

    # 品 -> 5
    txt = re.sub('品',
        r'5', txt)

    # B -> 8
    txt = re.sub('B',
        r'8', txt)

    # る -> 削除
    txt = re.sub('る',
        r'', txt)

    # D -> 0
    txt = re.sub('D',
        r'0', txt)

    # U -> 0
    txt = re.sub('U',
        r'0', txt)

    # ヨ伺 -> 9位
    txt = re.sub('ヨ伺',
        r'9位', txt)

    # 位 -> 削除
    txt = re.sub('位',
        r'', txt)
    txt = re.sub("\\D", "", txt)

    return txt


def apex_pick_tkill(img, cnt,fps,filename, color_val=[230,179,63], crop_flg=False ,crop_loc=(0,0,0,0)):

    img_org = img
    threshold = 70
    color_val=[230,179,0]
    img_rgb = img_org.convert("RGB")
    pixels = img_rgb.load()
    # 色相反転＆2諧調化
    r_pick_min = float(color_val[0]) - threshold
    g_pick_min = float(color_val[1]) - threshold
    b_pick_min = float(color_val[2]) - threshold
    r_pick_max = float(color_val[0]) + threshold
    g_pick_max = float(color_val[1]) + threshold
    b_pick_max = float(color_val[2]) + threshold
    for j in range(img_rgb.size[1]):
        for i in range(img_rgb.size[0]):
            if ( r_pick_min <= pixels[i, j][0] <= r_pick_max and g_pick_min <= pixels[i, j][1] <= g_pick_max and b_pick_min <= pixels[i, j][2] <= b_pick_max):
                pixels[i, j] = (0, 0, 0)
            else:
                pixels[i, j] = (255, 255, 255)
    image = img_rgb
     
    # 番号の部分を切り抜き
    if crop_flg:
        img_box = image.crop(crop_loc)
        image = img_box

    # out_path_image = "./result/tkill_" + os.path.basename(filename)
    # image.save(out_path_image)

    txt = tool.image_to_string(
        image,
        lang=lang,
        builder=pyocr.builders.TextBuilder(tesseract_layout=7)
    )

    # ]→1
    txt = re.sub(']',
        r'1', txt)

    # [→0
    txt = re.sub('\[',
        r'0', txt)

    # ロ→9
    txt = re.sub('ロ',
        r'9', txt)

    # う→3
    txt = re.sub('う',
        r'3', txt)

    # B -> 6
    txt = re.sub('B',
        r'6', txt)
    txt = re.sub("\\D", "", txt)

    return txt

def apex_pick_kill(img, cnt,fps,filename, color_val=[230,179,63], crop_flg=False ,crop_loc=(0,0,0,0)):

    img_org = img
    threshold = 70
    color_val=[230,179,0]
    img_rgb = img_org.convert("RGB")
    pixels = img_rgb.load()
    # 色相反転＆2諧調化
    r_pick_min = float(color_val[0]) - threshold
    g_pick_min = float(color_val[1]) - threshold
    b_pick_min = float(color_val[2]) - threshold
    r_pick_max = float(color_val[0]) + threshold
    g_pick_max = float(color_val[1]) + threshold
    b_pick_max = float(color_val[2]) + threshold
    for j in range(img_rgb.size[1]):
        for i in range(img_rgb.size[0]):
            if ( r_pick_min <= pixels[i, j][0] <= r_pick_max and g_pick_min <= pixels[i, j][1] <= g_pick_max and b_pick_min <= pixels[i, j][2] <= b_pick_max):
                pixels[i, j] = (0, 0, 0)
            else:
                pixels[i, j] = (255, 255, 255)
    image = img_rgb
     
    # 番号の部分を切り抜き
    if crop_flg:
        img_box = image.crop(crop_loc)
        image = img_box

    # out_path_image = "./result/kill_" + os.path.basename(filename)
    # image.save(out_path_image)

    txt = tool.image_to_string(
        image,
        lang='eng',
        builder=pyocr.builders.TextBuilder(tesseract_layout=7)
    )

    # ia] -> 0
    txt = re.sub('ia]',
        r'0', txt)

    # Oo -> 0
    txt = re.sub('Oo',
        r'0', txt)

    # B -> 6
    txt = re.sub('S',
        r'5', txt)

    # D -> 0
    txt = re.sub('D',
        r'0', txt)
    txt = re.sub("\\D", "", txt)


    return txt


def apex_pick_damage(img, cnt,fps,filename, color_val=[230,179,63], crop_flg=False ,crop_loc=(0,0,0,0)):

    img_org = img
    threshold = 70
    color_val=[230,179,0]
    img_rgb = img_org.convert("RGB")
    pixels = img_rgb.load()
    # # 色相反転＆2諧調化
    # r_pick_min = float(color_val[0]) - threshold
    # g_pick_min = float(color_val[1]) - threshold
    # b_pick_min = float(color_val[2]) - threshold
    # r_pick_max = float(color_val[0]) + threshold
    # g_pick_max = float(color_val[1]) + threshold
    # b_pick_max = float(color_val[2]) + threshold
    # for j in range(img_rgb.size[1]):
    #     for i in range(img_rgb.size[0]):
    #         if ( r_pick_min <= pixels[i, j][0] <= r_pick_max and g_pick_min <= pixels[i, j][1] <= g_pick_max and b_pick_min <= pixels[i, j][2] <= b_pick_max):
    #             pixels[i, j] = (0, 0, 0)
    #         else:
    #             pixels[i, j] = (255, 255, 255)
    # image = img_rgb
    image = img_rgb

    # 番号の部分を切り抜き
    if crop_flg:
        img_box = image.crop(crop_loc)
        image = img_box

    # out_path_image = "./result/damage_" + os.path.basename(filename)
    # image.save(out_path_image)

    # txt = tool.image_to_string(
    #     image,
    #     lang='eng',
    #     builder=pyocr.builders.TextBuilder(tesseract_layout=7),
    #     config='-c tessedit_char_whitelist=0123456789'
    # )

    txt = pytesseract.image_to_string(image, config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')
    txt = re.sub("\\D", "", txt)
    return txt

init_logger()
#getLogger().info("main start")

p = pathlib.Path(os.path.dirname(__file__))
program_path = str(p.resolve())
tools = pyocr.get_available_tools()
if len(tools) == 0:
    print("No OCR tool found")
    sys.exit(1)
tool = tools[0]
lang='jpn'

i=1
fps=60

#print(args.crop)

# 原稿画像の読み込み
img_org = Image.open(args.src)
#img_rgb = img_org.convert("RGB")
img_rgb = img_org
img_resize = img_rgb.resize((1920,1080))

#print(img_resize, i,fps, 'debug', args.flg_threshold, args.threshold, args.flg_crop, args.crop)

# クロップなし全画面
#txt = apex_ocr(img_resize, i,fps, args.src, 'debug', args.flg_threshold, args.threshold, args.flg_crop, args.crop)
place = apex_pick_place(img_resize, i,fps, args.src, [230, 179, 63], True, [1311, 120, 1560, 182])
if not place:
    place='null'
tkill = apex_pick_tkill(img_resize, i,fps, args.src, [230, 179, 63], True, [1595, 120, 1811, 182])
if not tkill:
    tkill='null'
kill = apex_pick_kill(img_resize, i,fps, args.src, [230, 179, 63], True, [723, 329, 826, 436])
if not kill:
    kill='null'
damage = apex_pick_damage(img_resize, i,fps, args.src, [230, 179, 63], True, [723, 477, 810, 515])
if not damage:
    damage='null'
print("%s %s %s %s" % (place,tkill,kill,damage))
#print("place_%s_tkill_%s_kill_%s_damage_%s" % (place,tkill,kill,damage))
#result_a,this_no_start = apex_search(txt, 'memberlist', '部隊メンバー', i , '1',fps,match)

# アリーナチャンピオン
#txt = apex_ocr(img_resize, i,fps, 'debug', False, [0,0,0], True, [708, 125, 1226, 182])
#print(txt)


