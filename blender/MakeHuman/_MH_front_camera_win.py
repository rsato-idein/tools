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

# レンダリング設定
bpy.context.scene.render.resolution_x = 128
bpy.context.scene.render.resolution_y = 128

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
bpy.context.edit_object.data.edit_bones['head'].select = True
bpy.ops.armature.parent_clear(type='CLEAR')
root_bone = bpy.context.edit_object.data.edit_bones['Root']
root_bone.tail[0] = root_bone.head[0] = head_x
root_bone.tail[2] = root_bone.tail[1]
root_bone.tail[1] = 0
root_bone.roll = radians(90)
bpy.ops.object.mode_set(mode='OBJECT')
obj.location = (-head_x, -head_y, -head_z)
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
mask.location = (0.07, 0, -0.02)
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


save_dir = os.path.join(WORK_DIR, 'human_front_camera', FBX_NO)
os.makedirs(save_dir, exist_ok=True)
tait_bryan = False
for yaw_ in range(-180, 180, INTERVAL):
    bpy.ops.object.mode_set(mode='POSE')
    for pitch_ in range(-90, 90, INTERVAL):
        for roll_ in range(-90, 90, INTERVAL):
            # 角度の修正
            pitch = pitch_ + np.random.random() * INTERVAL * 0
            yaw = yaw_ + np.random.random() * INTERVAL * 0
            roll = roll_ + np.random.random() * INTERVAL * 0
            if not (-50 <= pitch <= 60 and -50 <= roll <= 50):
                continue

            R = get_R(pitch, yaw, roll)

            head.rotation_euler = (radians(pitch), radians(yaw), radians(roll))
            root.rotation_euler = (radians(0), radians(yaw), radians(0))

            mask_flg = np.random.rand() < MASK_RATE
            if mask_flg:
                # マスク色変更
                is_mask_white = np.random.rand() > 0.5
                for key in ['FaceMask_Main', 'FaceMask_ElasticBand_Left', 'FaceMask_ElasticBand_Right']:
                    bpy.data.objects[key].active_material = mask_white if is_mask_white else mask_black
                    bpy.data.objects[key].hide_render = False
            else:
                # マスク非着用
                for key in ['FaceMask_Main', 'FaceMask_ElasticBand_Left', 'FaceMask_ElasticBand_Right']:
                    bpy.data.objects[key].hide_render = True

            # 保存
            if tait_bryan:
                pitch = -pitch
                yaw = -yaw
            save_name = '_'.join([
                FBX_NO, BG_NO, f'p{round(pitch):+04}', f'y{round(yaw):+04}', f'r{round(roll):+04}',
                f'wp{round(pitch):+04}', f'wy{round(yaw):+04}', f'wr{round(roll):+04}'
            ]) + '.png'
            if mask_flg:
                save_name = save_name.replace('.png', '_mask.png')
            save_path = os.path.join(save_dir, save_name)
            bpy.context.scene.render.filepath = save_path
            bpy.ops.render.render(write_still=True)
            with open(save_path.replace('.png', '.json'), 'w') as f:
                json.dump({
                    'pitch': pitch,
                    'yaw': yaw,
                    'roll': roll,
                    'mask': mask_flg,
                    'mask_color': ('white' if is_mask_white else 'black') if mask_flg else 'none'
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
