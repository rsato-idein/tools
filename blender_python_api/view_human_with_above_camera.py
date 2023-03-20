import json
import os
from math import radians

import bpy
import numpy as np

# 解像度を変更
bpy.context.scene.render.resolution_x = 2048
bpy.context.scene.render.resolution_y = 1536

# カメラ設定
cam = bpy.data.objects['Camera']
cam.location = (2, 0, 4)
cam.rotation_euler = (radians(60), radians(0), radians(90))
cam.data.lens = 22
cam.data.clip_end = 15

# ライト設定
light = bpy.data.objects['Light']
light.location = (2, 0, 5)
light.rotation_euler = (radians(0), radians(0), radians(0))

# human 設定
obj = bpy.data.objects['MakeHuman default skeleton']
obj.location = (0, 0, 0)
obj.rotation_mode = 'ZYX'
obj.rotation_euler = (radians(90), radians(90), radians(0))

# レンダリング
save_dir = f'/Users/rsato/Documents/Blender/human_above_camera'
os.makedirs(save_dir, exist_ok=True)

bpy.ops.render.render()
save_path = f'{save_dir}/pose.png'
bpy.data.images['Render Result'].save_render(filepath=save_path)
