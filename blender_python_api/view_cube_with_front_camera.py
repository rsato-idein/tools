import json
import os
from math import radians

import bpy
import numpy as np

# 解像度を変更
bpy.context.scene.render.resolution_x = 256
bpy.context.scene.render.resolution_y = 256

# カメラ設定
cam = bpy.data.objects['Camera']
cam.location = (10, 0, 0)
cam.rotation_euler = (radians(90), radians(0), radians(90))
cam.data.lens = 100
cam.data.clip_end = 15

# ライト設定
light = bpy.data.objects['Light']
light.location = (2, 0, 5)
light.rotation_euler = (radians(0), radians(0), radians(0))

# cube 設定
cube = bpy.data.objects['Cube']
cube.scale = (1, 1, 1)
cube.location = (0, 0, 0)
cube.rotation_mode = 'ZYX'

# order: yaw, pitch, roll
save_dir = f'/Users/rsato/Documents/Blender/cube_front_camera'
tait_bryan = False
os.makedirs(save_dir, exist_ok=True)
interval = 30
for yaw in range(-180, 181, interval):
    for pitch in range(-90, 91, interval):
        pitch = np.clip(pitch, -90 + 1e-6, 90 - 1e-6)
        for roll in range(-180, 181, interval):
            cube.rotation_euler = (radians(roll), radians(pitch), radians(yaw))

            # レンダリング
            bpy.ops.render.render()

            # 保存
            if tait_bryan:
                pitch = -pitch
                yaw = -yaw
            save_path = f'{save_dir}/pose_{round(pitch)}_{round(yaw)}_{round(roll)}.png'
            bpy.data.images['Render Result'].save_render(filepath=save_path)
            with open(save_path.replace('.png', '.json'), 'w') as f:
                json.dump({
                    'pitch': pitch,
                    'yaw': yaw,
                    'roll': roll
                }, f)

cube.rotation_euler = (radians(0), radians(0), radians(0))
