# blender -b -P MH_front_camera.py -- 001 01 90 --cycles-device CUDA

import json
import os
import sys
from math import radians

import bpy
import numpy as np
from PIL import Image, ImageFilter

WORK_DIR = os.path.dirname(__file__)
FBX_NO = sys.argv[5]
BG_NO = sys.argv[6]
INTERVAL = int(sys.argv[7])
FBX_OBJ_NAME = 'Game_engine'

# レンダリング設定
bpy.context.scene.render.resolution_x = 128
bpy.context.scene.render.resolution_y = 128
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.use_preview_adaptive_sampling = False
bpy.context.scene.cycles.use_adaptive_sampling = False
bpy.context.scene.cycles.preview_samples = 8
bpy.context.scene.cycles.samples = 32
bpy.context.scene.cycles.max_bounces = 4
bpy.context.scene.cycles.diffuse_bounces = 3
bpy.context.scene.cycles.glossy_bounces = 3
bpy.context.scene.cycles.transmission_bounces = 3
bpy.context.scene.render.use_persistent_data = True
bpy.context.scene.world.cycles.sampling_method = 'MANUAL'
bpy.context.scene.world.cycles.sample_map_resolution = 512
bpy.context.scene.render.threads_mode = 'FIXED'
bpy.context.scene.render.threads = 6

# Cube 削除
bpy.ops.object.select_all(action='DESELECT')
if 'Cube' in bpy.data.objects:
    bpy.data.objects['Cube'].select_set(True)
    bpy.ops.object.delete()

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
light.data.type = 'SUN'
light.data.energy = 20
light.cycles.cast_shadow = False
light.data.angle = radians(120)

# obj 設定
if FBX_OBJ_NAME not in bpy.data.objects:
    obj_path = os.path.join(WORK_DIR, 'models', FBX_NO, 'human.fbx')
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
head_x, head_y, head_z = head_bone.head
head_bone.roll = radians(90)
bpy.ops.armature.select_all(action='DESELECT')
bpy.context.edit_object.data.edit_bones['neck_01'].select = True
bpy.ops.armature.switch_direction()
bpy.ops.object.mode_set(mode='OBJECT')
obj.location = (-head_x, -head_y, -head_z)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.scene.render.film_transparent = True

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


save_dir = os.path.join(WORK_DIR, 'human_front_camera', FBX_NO)
os.makedirs(save_dir, exist_ok=True)
tait_bryan = False
bg = Image.open(os.path.join(WORK_DIR, 'background', f'fm{BG_NO}.png')).convert('RGBA')
for yaw in range(-180, 180, INTERVAL):
    bpy.ops.object.mode_set(mode='POSE')
    for pitch in range(-60, 61, INTERVAL):
        if not -50 <= pitch <= 60:
            continue
        for roll in range(-60, 61, INTERVAL):
            if not -50 <= roll <= 50:
                continue
            R = get_R(pitch, yaw, roll)

            # 剛体変換
            obj.rotation_euler[2] = radians(yaw)
            bpy.ops.object.mode_set(mode='EDIT')
            head_bone = bpy.context.edit_object.data.edit_bones['head']
            head_bone.roll = radians(90 - yaw)
            bpy.ops.object.mode_set(mode='POSE')

            theta = np.arccos(R[2, 0]) - np.pi/2
            head.rotation_euler = (radians(pitch), 0, radians(roll))
            neck.rotation_euler = (-(max(0, theta/90*45)), 0, 0)
            spine.location[2] = -0.1 * max(theta, 0) / np.pi * 2

            # 保存
            if tait_bryan:
                pitch = -pitch
                yaw = -yaw
            save_path = os.path.join(
                save_dir,
                f'{FBX_NO}_{BG_NO}_p{round(pitch):+04}_y{round(yaw):+04}_r{round(roll):+04}.png'
            )
            bpy.context.scene.render.filepath = save_path
            bpy.ops.render.render(write_still=True)
            img = Image.open(save_path)
            edge = np.random.randint(128, 256)
            l = np.random.randint(0, bg.size[0]-edge)
            t = np.random.randint(256, bg.size[1]-edge-256)
            r = l + edge
            b = t + edge
            random_bg = bg.crop((l, t, r, b)).resize((128, 128), Image.BILINEAR)
            img = Image.alpha_composite(random_bg, img)
            img.convert('RGB').save(save_path.replace('.png', '.jpg'))
            os.remove(save_path)
            with open(save_path.replace('.png', '.json'), 'w') as f:
                json.dump({
                    'pitch': pitch,
                    'yaw': yaw,
                    'roll': roll
                }, f)

bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.delete()
