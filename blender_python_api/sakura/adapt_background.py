# /bin/3.3/python/bin/python3.10 adapt_background.py 001

import os
import sys
from random import randint
from shutil import copy

import numpy as np
from PIL import Image, ImageFilter

WORK_DIR = os.path.dirname(__file__)
FBX_NO = sys.argv[1]
SRC_DIR = os.path.join(WORK_DIR, 'human_front_camera')
DST_DIR = os.path.join(WORK_DIR, 'human_front_camera_fm')
os.makedirs(DST_DIR, exist_ok=True)

bg = Image.open(os.path.join(WORK_DIR, 'background', f'fm{FBX_NO}.png'))
W, H = bg.size
for cur_dir, _, file_names in os.walk(SRC_DIR):
    for file_name in file_names:
        src_path = os.path.join(cur_dir, file_name)
        dst_path = src_path.replace(SRC_DIR, DST_DIR)
        if src_path.endswith('.png'):
            edge = randint(128, 256)
            l = randint(0, W-edge)
            t = randint(256, H-edge-256)
            r = l + edge
            b = t + edge
            random_bg = bg.crop((l, t, r, b)).resize((128, 128))
            img = Image.open(src_path)
            img = img.filter(filter=ImageFilter.GaussianBlur(1))
            img = Image.alpha_composite(random_bg.convert('RGBA'), img)
            img.save(dst_path)
        else:
            copy(src_path, dst_path)
