import argparse
import os
from subprocess import run

import numpy as np
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('s', type=int)
parser.add_argument('e', type=int)
parser.add_argument('i', type=int)
args = parser.parse_args()

for fbx_no in tqdm(range(args.s, args.e+1)):
    fbx_no = f'{fbx_no:03}'
    bg_no = f'{np.random.randint(1, 11):02}'
    run(['blender', '-b', '-P', 'MH_front_camera.py', '--', fbx_no, bg_no, str(args.i), '--cycles-device', 'CUDA'], stdout=open(os.devnull, 'wb'))
