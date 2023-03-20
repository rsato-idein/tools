import json
import os
from math import radians

import bpy
import numpy as np

# 解像度を変更
bpy.context.scene.render.resolution_x = 256
bpy.context.scene.render.resolution_y = 256

if 'Cube' in bpy.data.objects:
    bpy.data.objects['Cube'].select_set(True)
    bpy.ops.object.delete()

# カメラ設定
cam = bpy.data.objects['Camera']
cam.location = (0.75, 0, 0)
#cam.rotation_euler = (radians(90), radians(0), radians(90))
#cam.data.lens = 100
#cam.data.clip_end = 15

# ライト設定
light = bpy.data.objects['Light']
light.location = (5, 0, 0)
light.rotation_euler = (radians(0), radians(0), radians(0))

# obj 設定
obj = bpy.data.objects['MakeHuman default skeleton']
obj.rotation_mode = 'ZYX'
obj.rotation_euler = (radians(0), radians(90), radians(90))
obj.location = (0, 0, -0.8)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)

bpy.ops.render.render()
bpy.data.images['Render Result'].save_render(filepath='/Users/rsato/Documents/Blender/a.png')

# order: yaw, pitch, roll
#save_dir = f'/Users/rsato/Documents/Blender/human_front_camera'
#tait_bryan = False
#os.makedirs(save_dir, exist_ok=True)
#interval = 30
#for yaw in range(-180, 181, interval):
#    for pitch in range(-90, 91, interval):
#        pitch = np.clip(pitch, -90 + 1e-6, 90 - 1e-6)
#        for roll in range(-180, 181, interval):
#            obj.rotation_euler = (radians(roll), radians(pitch), radians(yaw))

#            # レンダリング
#            bpy.ops.render.render()

#            # 保存
#            if tait_bryan:
#                pitch = -pitch
#                yaw = -yaw
#            save_path = f'{save_dir}/pose_{round(pitch)}_{round(yaw)}_{round(roll)}.png'
#            bpy.data.images['Render Result'].save_render(filepath=save_path)
#            with open(save_path.replace('.png', '.json'), 'w') as f:
#                json.dump({
#                    'pitch': pitch,
#                    'yaw': yaw,
#                    'roll': roll
#                }, f)

#obj.rotation_euler = (radians(0), radians(0), radians(0))
