import json
import os
from math import radians
from shutil import rmtree

import bpy
import numpy as np

WORK_DIR = os.path.join(
    os.environ['HOMEPATH'], 'Works', 'tools', 'blender_python_api'
)
FBX_FILE_NAME = '001'
FBX_OBJ_NAME = 'Game_engine'


# Cube 削除
bpy.ops.object.select_all(action='DESELECT')
if 'Cube' in bpy.data.objects:
    bpy.data.objects['Cube'].select_set(True)
    bpy.ops.object.delete()

# 解像度を変更
bpy.context.scene.render.resolution_x = 256
bpy.context.scene.render.resolution_y = 256

# カメラ設定
cam = bpy.data.objects['Camera']
cam.location = (1, 0, 0)
cam.rotation_mode = 'XYZ'
cam.rotation_euler = (radians(90), radians(0), radians(90))
cam.scale = (0.1, 0.1, 0.1)
cam.data.lens = 100
cam.data.clip_end = 15

# ライト設定
light = bpy.data.objects['Light']
light.location = (5, 0, 0)
light.rotation_euler = (radians(0), radians(0), radians(0))

# obj 設定
if FBX_OBJ_NAME not in bpy.data.objects:
    obj_path = os.path.join(WORK_DIR, 'MF', f'{FBX_FILE_NAME}.fbx')
    bpy.ops.import_scene.fbx(filepath=obj_path)

obj = bpy.data.objects[FBX_OBJ_NAME]
obj.scale = (0.01, 0.01, 0.01)
obj.rotation_mode = 'ZYX'
obj.rotation_euler = (0, 0, 0)
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.transforms_clear()
bpy.ops.object.mode_set(mode='OBJECT')
obj.rotation_euler[2] = radians(90)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.mode_set(mode='EDIT')
head_bone = bpy.context.edit_object.data.edit_bones['head']
head_bone.tail[0] = head_bone.head[0]
hx, hy, hz = head_bone.head
head_bone.roll = radians(90)
bpy.ops.armature.select_all(action='DESELECT')
bpy.context.edit_object.data.edit_bones['neck_01'].select = True
bpy.ops.armature.switch_direction()
bpy.ops.object.mode_set(mode='OBJECT')
obj.location = (-hx, -hy, -hz)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 回転 yaw -> pitch -> roll
bpy.ops.object.mode_set(mode='OBJECT')
obj = bpy.data.objects[FBX_OBJ_NAME]
head = obj.pose.bones['head']
neck = obj.pose.bones['neck_01']
spine = obj.pose.bones['spine_01']
obj.rotation_mode = 'ZYX'
head.rotation_mode = neck.rotation_mode = 'YXZ'


def get_R(p, y, r):
    sp, sy, sr = np.sin(np.deg2rad([p, y, r]))
    cp, cy, cr = np.cos(np.deg2rad([p, y, r]))
    R = np.array([
        [cp * cy, -cp * sy, sp],
        [cr * sy + sr * sp * cy, cr * cy - sr * sp * sy, -sr * cp],
        [sr * sy - cr * sp * cy, cy * sr + cr * sp * sy, cr * cp]
    ])
    return R


save_dir = os.path.join(WORK_DIR, 'human_front_camera')
rmtree(save_dir, ignore_errors=True)
os.makedirs(save_dir)
tait_bryan = False
interval = 90
for yaw in range(-180, 180, interval):
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.rotation_euler[2] = radians(yaw)
    bpy.ops.object.mode_set(mode='EDIT')
    head_bone = bpy.context.edit_object.data.edit_bones['head']
    head_bone.roll = radians(90 - yaw)
    bpy.ops.object.mode_set(mode='POSE')
    for pitch in range(-90, 91, interval):
        pitch = np.clip(pitch, -90 + 1e-6, 90 - 1e-6)
        for roll in range(-90, 90, interval):
            R = get_R(pitch, yaw, roll)
            theta = np.arccos(R[2, 0]) - np.pi/2
            head.rotation_euler = (radians(pitch), 0, radians(roll))
            neck.rotation_euler = (-(max(0, theta/3)), 0, 0)
            spine.location[2] = -0.1 * max(theta, 0) / np.pi * 2

            # レンダリング
            bpy.ops.render.render()

            # 保存
            if tait_bryan:
                pitch = -pitch
                yaw = -yaw
            save_path = os.path.join(
                save_dir, f'{FBX_FILE_NAME}_p{round(pitch):+04}_y{round(yaw):+04}_r{round(roll):+04}.png')
            bpy.data.images['Render Result'].save_render(filepath=save_path)
            with open(save_path.replace('.png', '.json'), 'w') as f:
                json.dump({
                    'pitch': pitch,
                    'yaw': yaw,
                    'roll': roll
                }, f)

bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.delete()
