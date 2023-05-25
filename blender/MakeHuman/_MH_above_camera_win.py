import json
import os
from math import radians

import bpy
import numpy as np

WORK_DIR = os.path.join(
    os.environ['HOMEPATH'], 'Works', 'tools', 'blender', 'MakeHuman'
)
FBX_NO = '001'
BG_NO = '01'
MASK_RATE = 0.8
INTERVAL = 45
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
bpy.context.edit_object.data.edit_bones['head'].select = True
bpy.ops.armature.parent_clear(type='CLEAR')
root_bone = bpy.context.edit_object.data.edit_bones['Root']
root_bone.tail[0] = root_bone.head[0] = head_x
root_bone.tail[2] = root_bone.tail[1]
root_bone.tail[1] = 0
root_bone.roll = radians(90)
bpy.ops.object.mode_set(mode='OBJECT')
obj.location = (-head_x, -head_y, 0)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.scene.render.film_transparent = True

# 回転 yaw -> pitch -> roll
bpy.ops.object.mode_set(mode='OBJECT')
obj = bpy.data.objects[FBX_OBJ_NAME]
head = obj.pose.bones['head']
root = obj.pose.bones['Root']
obj.rotation_mode = 'ZYX'
head.rotation_mode = root.rotation_mode = 'YXZ'

# マスク読み込み
mask_path = os.path.join(WORK_DIR, 'models', 'mask', 'face-mask.fbx')
bpy.ops.import_scene.fbx(filepath=mask_path)
mask = bpy.data.objects['FaceMask']
mask.scale = (0.006, 0.005, 0.005)
mask.rotation_mode = 'YXZ'
mask.rotation_euler = (radians(90), radians(90), radians(0))
mask.location = (0.07, 0, head_z-0.02)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# マスクの着用
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects[FBX_OBJ_NAME].select_set(True)
bpy.ops.object.mode_set(mode='POSE')
armature = bpy.context.active_object
bpy.ops.pose.select_all(action='DESELECT')
head_bone = armature.pose.bones.get('head')
head_bone.bone.select = True
armature.data.bones.active = head_bone.bone
bpy.data.objects.get('FaceMask').select_set(True)
bpy.context.view_layer.objects.active = armature
bpy.ops.object.parent_set(type='BONE')

# マスクカラーマテリアル作成
mask_white = bpy.data.materials.new('White')
mask_white.use_nodes = True
mask_white.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (0.5, 0.5, 0.5, 1.0)
mask_black = bpy.data.materials.new('Black')
mask_black.use_nodes = True
mask_black.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (0.01, 0.01, 0.01, 1.0)


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
for yaw_ in range(-180, 180, INTERVAL):
    bpy.ops.object.mode_set(mode='POSE')
    for pitch_ in range(-90, 90, INTERVAL):
        pitch_ = np.clip(pitch_, -89, 89)
        for roll_ in range(-90, 90, INTERVAL):
            # 角度の修正
            pitch = pitch_ + np.random.random() * INTERVAL * 0
            yaw = yaw_ + np.random.random() * INTERVAL * 0
            roll = roll_ + np.random.random() * INTERVAL * 0
            if not (-50 <= pitch <= 60 and -50 <= roll <= 50):
                continue

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
            R = Rs_tb @ Rs_lr @ Rc_inv @ get_R(pitch, yaw, roll)
            p, y, r = get_euler(R)

            head.rotation_euler = (radians(pitch), radians(yaw), radians(roll))
            root.rotation_euler = (radians(0), radians(yaw), radians(0))

            obj.location = obj_location

            if np.random.rand() < MASK_RATE:
                # マスク色変更
                is_mask_white = np.random.rand() > 0.5
                for key in ['FaceMask_Main', 'FaceMask_ElasticBand_Left', 'FaceMask_ElasticBand_Right']:
                    bpy.data.objects[key].active_material = mask_white if is_mask_white else mask_black
                    bpy.data.objects[key].hide_render = False
            else:
                # マスク非着用
                for key in ['FaceMask_Main', 'FaceMask_ElasticBand_Left', 'FaceMask_ElasticBand_Right']:
                    bpy.data.objects[key].hide_render = True

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
                p = -p
                y = -y
            save_path = os.path.join(
                save_dir,
                f'{FBX_NO}_{BG_NO}_p{round(p):+04}_y{round(y):+04}_r{round(r):+04}_wp{round(pitch):+04}_wy{round(yaw):+04}_wr{round(roll):+04}.png'
            )
            bpy.context.scene.render.filepath = save_path
            bpy.ops.render.render(write_still=True)
            with open(save_path.replace('.png', '.json'), 'w') as f:
                json.dump({
                    'pitch': p,
                    'yaw': y,
                    'roll': r,
                    'bbox': [xmin, ymin, xmax, ymax],
                    'world_pose': [pitch, yaw, roll]
                }, f)

bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
obj = bpy.data.objects[FBX_OBJ_NAME]
obj.select_set(True)
for child in obj.children:
    child.select_set(True)
for child in bpy.data.objects['FaceMask'].children:
    child.select_set(True)
bpy.ops.object.delete()
