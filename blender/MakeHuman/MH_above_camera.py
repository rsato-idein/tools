# blender -b -P MH_above_camera.py -- 001 01 90 --cycles-device CUDA

import json
import os
import sys
from math import radians

import bpy
import numpy as np
from PIL import Image

WORK_DIR = os.path.dirname(__file__)
FBX_NO = sys.argv[5]
BG_NO = sys.argv[6]
INTERVAL = sys.argv[7]
FBX_OBJ_NAME = 'Game_engine'
SPACE_DEPTH = 8
CAM_SETTING = {
    '01': {
        'loc': (2, 0, 3),
        'rot': (radians(0), radians(70), radians(90))
    },
    '02': {
        'loc': (2, 0, 4),
        'rot': (radians(20), radians(65), radians(55))
    },
    '03': {
        'loc': (2, 0, 3),
        'rot': (radians(-12), radians(65), radians(110))
    },
    '04': {
        'loc': (2, 0, 3),
        'rot': (radians(-20), radians(68), radians(110))
    },
    '05': {
        'loc': (2, 0, 3),
        'rot': (radians(-3), radians(70), radians(90))
    },
    '06': {
        'loc': (2, 0, 3),
        'rot': (radians(5), radians(65), radians(80))
    },
    '07': {
        'loc': (2, 0, 3),
        'rot': (radians(0), radians(65), radians(90))
    },
    '08': {
        'loc': (2, 0, 3),
        'rot': (radians(8), radians(70), radians(78))
    },
    '09': {
        'loc': (2, 0, 3),
        'rot': (radians(0), radians(68), radians(90))
    },
    '10': {
        'loc': (2, 0, 3),
        'rot': (radians(20), radians(80), radians(70))
    },
}

# レンダリング設定
bpy.context.scene.render.resolution_x = W = 2048
bpy.context.scene.render.resolution_y = H = 1536
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
bpy.context.scene.render.threads = 4

# Cube 削除
bpy.ops.object.select_all(action='DESELECT')
if 'Cube' in bpy.data.objects:
    bpy.data.objects['Cube'].select_set(True)
    bpy.ops.object.delete()

# カメラ設定
cam = bpy.data.objects['Camera']
cam.location = CAM_SETTING[BG_NO]['loc']
cam.rotation_mode = 'ZYX'
cam.rotation_euler = CAM_SETTING[BG_NO]['rot']
cam.data.lens = fx = fy = 22
cam.data.clip_end = 15
cam.data.sensor_width = w = 36
cam.data.sensor_height = h = 27

# ライト設定
light = bpy.data.objects['Light']
light.location = (0, 0, 3)
light.rotation_euler = (radians(0), radians(0), radians(0))
light.data.type = 'SUN'
light.data.energy = 20
light.cycles.cast_shadow = False
light.data.angle = radians(120)

# obj 設定
if FBX_OBJ_NAME not in bpy.data.objects:
    obj_path = os.path.join(WORK_DIR, 'MF', FBX_NO, 'human.fbx')
    bpy.ops.import_scene.fbx(filepath=obj_path)

obj = bpy.data.objects[FBX_OBJ_NAME]
obj.scale = (0.01, 0.01, 0.01)
obj.rotation_mode = 'ZYX'
obj.rotation_euler = (0, 0, 0)
# if 'COV-Mask' in bpy.data.materials:
#     mask_color = (0, 0, 0, 1) if np.random.random() < 0.5 else (1, 1, 1, 1)
#     bpy.data.materials['COV-Mask'].node_tree.nodes['Principled BSDF'].inputs[0].default_value = mask_color
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
obj.location = (-head_x, -head_y, 0)
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


def get_euler(R):
    p = np.arcsin(R[0, 2])
    y = np.arctan2(-R[0, 1], R[0, 0])
    r = np.arctan2(-R[1, 2], R[2, 2])
    return np.rad2deg([p, y, r])


def get_Ry(theta):
    theta = np.deg2rad(theta)
    return np.array([
        [np.cos(theta), 0, np.sin(theta)],
        [0, 1, 0],
        [-np.sin(theta), 0, np.cos(theta)],
    ])


def get_Rz(theta):
    theta = np.deg2rad(theta)
    return np.array([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta), np.cos(theta), 0],
        [0, 0, 1],
    ])


save_dir = os.path.join(WORK_DIR, 'human_above_camera', FBX_NO)
os.makedirs(save_dir, exist_ok=True)
tait_bryan = False
Rc_inv = np.linalg.inv(np.array(cam.rotation_euler.to_matrix()) @ np.linalg.inv(get_R(90, 90, 0)))
bg = Image.open(os.path.join(WORK_DIR, 'background', f'fm{BG_NO}.png')).convert('RGBA')
for yaw_ in range(-180, 180, INTERVAL):
    bpy.ops.object.mode_set(mode='POSE')
    for pitch_ in range(-90, 90, INTERVAL):
        pitch_ = np.clip(pitch_, -89, 89)
        for roll_ in range(-90, 90, INTERVAL):
            # 角度の修正
            pitch = pitch_ + np.random.random() * INTERVAL
            yaw = yaw_ + np.random.random() * INTERVAL
            roll = roll_ + np.random.random() * INTERVAL

            # location の設定
            Xo = np.random.random() * -SPACE_DEPTH
            Yo = np.random.random() * 2 - 1
            if -2 < Xo <= -1:
                Yo *= 2
            elif Xo <= -2:
                Yo *= 3
            obj_location = (Xo, Yo, 0)
            head_location = (Xo, Yo, head_z)

            # 角度再計算
            Xc, Yc, Zc = (Rc_inv @ (np.array(head_location) - np.array(cam.location)).reshape(-1, 1)).flatten()
            Rs_tb = get_Ry(np.rad2deg(np.arctan(Zc/Xc)))
            Rs_lr = get_Rz(np.rad2deg(np.arctan(-Yc/Xc)))
            Rc = get_R(pitch, yaw, roll)
            R = np.linalg.inv(Rs_tb @ Rs_lr @ Rc_inv) @ Rc
            p, y, r = get_euler(R)

            # 剛体変換
            obj.rotation_euler[2] = radians(yaw)
            bpy.ops.object.mode_set(mode='EDIT')
            head_bone = bpy.context.edit_object.data.edit_bones['head']
            head_bone.roll = radians(90 - yaw)
            bpy.ops.object.mode_set(mode='POSE')

            theta = np.arccos(R[2, 0]) - np.pi/2
            head.rotation_euler = (radians(p), radians(y-yaw), radians(r))
            neck.rotation_euler = (-(max(0, theta/90*45)), 0, 0)
            spine.location[2] = -0.1 * max(theta, 0) / np.pi * 2

            obj.location = obj_location

            # BBox 領域計算
            cx = W * (0.5 - (fx * Yc) / (w * Xc))
            cy = H * (0.5 + (fy * Zc) / (h * Xc))
            s = W * fx / (w * abs(Xc)) * 0.3
            xmin, ymin, xmax, ymax = int(cx-s/2), int(cy-s/2), int(cx+s/2), int(cy+s/2)

            # レンダリング
            bbox = obj.bound_box
            bpy.context.scene.render.use_border = True
            bpy.context.scene.render.border_min_x = (cx-s/2) / W - 0.05
            bpy.context.scene.render.border_max_x = (cx+s/2) / W + 0.05
            bpy.context.scene.render.border_min_y = 1 - (cy+s/2) / H - 0.05
            bpy.context.scene.render.border_max_y = 1 - (cy-s/2) / H + 0.05

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
            img = Image.alpha_composite(bg, img)
            img.crop((xmin, ymin, xmax, ymax)).resize((256, 256), Image.BILINEAR).convert('RGB').save(save_path.replace('.png', '.jpg'))
            os.remove(save_path)
            with open(save_path.replace('.png', '.json'), 'w') as f:
                json.dump({
                    'pitch': pitch,
                    'yaw': yaw,
                    'roll': roll,
                    'bbox': [xmin, ymin, xmax, ymax],
                    'world_pose': [p, y, r]
                }, f)

bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.delete()
