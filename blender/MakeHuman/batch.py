import argparse
from subprocess import run

import numpy as np
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('s', type=int)
parser.add_argument('e', type=int)
args = parser.parse_args()

for fbx_no in tqdm(range(args.s, args.e+1)):
    fbx_no = f'{fbx_no:03}'
    bg_no = f'{np.random.randint(1, 11):02}'
    run(['blender', '-b', '-P', 'MH_above_camera.py', '--', fbx_no, bg_no, '--cycles-device', 'CUDA'])
