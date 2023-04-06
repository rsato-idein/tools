import json
import os
from math import radians
from shutil import rmtree

import bpy
import numpy as np

WORK_DIR = os.path.join(
    os.environ['HOMEPATH'], 'Works', 'tools', 'blender_python_api'
)
FBX_NO = '001'
FBX_OBJ_NAME = 'Game_engine'


# Cube 削除
bpy.ops.object.select_all(action='DESELECT')
if 'Cube' in bpy.data.objects:
    bpy.data.objects['Cube'].select_set(True)
    bpy.ops.object.delete()

# 解像度を変更
bpy.context.scene.render.resolution_x = 2048
bpy.context.scene.render.resolution_y = 1536

# カメラ設定
cam = bpy.data.objects['Camera']
cam.location = (2, 0, 3)
cam.rotation_mode = 'XYZ'
cam.rotation_euler = (radians(70), radians(0), radians(90))
cam.data.lens = 22
cam.data.clip_end = 15
cam.data.sensor_width = 36
cam.data.sensor_height = 27

# ライト設定
light = bpy.data.objects['Light']
light.location = (0, 0, 4)
light.rotation_euler = (radians(0), radians(0), radians(0))

# obj 設定
if FBX_OBJ_NAME not in bpy.data.objects:
    obj_path = os.path.join(WORK_DIR, 'MF', FBX_NO, 'human.fbx')
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
obj.location = (-hx, -hy, 0)
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

save_dir = os.path.join(WORK_DIR, 'human_above_camera')
rmtree(save_dir, ignore_errors=True)
os.makedirs(save_dir)
tait_bryan = False
interval = 90
Rc_inv = np.linalg.inv(get_R(-20, 0, 0))
bpy.context.scene.render.film_transparent = True
for yaw in range(-0, 1, interval):
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.rotation_euler[2] = radians(yaw)
    bpy.ops.object.mode_set(mode='EDIT')
    head_bone = bpy.context.edit_object.data.edit_bones['head']
    head_bone.roll = radians(90 - yaw)
    bpy.ops.object.mode_set(mode='POSE')
    for pitch in range(-0, 1, interval):
        pitch = np.clip(pitch, -90 + 1e-6, 90 - 1e-6)
        for roll in range(-0, 1, interval):
            
            # location の設定
            obj.location[0] = np.random.random() * -10
            obj.location[1] = np.random.random() * 2 - 1
            if -2 < obj.location[0] <= -1:
                obj.location[1] *= 2
            elif obj.location[0] <= -2:
                obj.location[1] *= 3
            head_location = (obj.location[0], obj.location[1], hz)

            Ro = get_R(pitch, yaw, roll)
            theta = np.arccos(Ro[2, 0]) - np.pi/2
            head.rotation_euler = (radians(pitch), 0, radians(roll))
            neck.rotation_euler = (-(max(0, theta/3)), 0, 0)
            spine.location[2] = -0.1 * max(theta, 0) / np.pi * 2

            # 角度再計算
            Hx, Hy, Hz = (Rc_inv @ (np.array(head_location) -
                          np.array(cam.location)).reshape(-1, 1)).flatten()
            Ry = get_Ry(np.rad2deg(np.arctan(Hz/Hx)))
            Rz = get_Rz(np.rad2deg(np.arctan(-Hy/Hx)))
            pitch, yaw, roll = map(float, get_euler(Rz @ Ry @ Rc_inv @ Ro))

            # BBox 領域計算
            cx = bpy.context.scene.render.resolution_x * \
                (0.5 - cam.data.lens*Hy/cam.data.sensor_width/Hx)
            cy = bpy.context.scene.render.resolution_y * \
                (0.5 + cam.data.lens*Hz/cam.data.sensor_height/Hx)
            s = bpy.context.scene.render.resolution_x * \
                cam.data.lens / cam.data.sensor_width / abs(Hx) * 0.3
            xmin, ymin, xmax, ymax = int(
                cx-s/2), int(cy-s/2), int(cx+s/2), int(cy+s/2)

#            # render
#            bbox = obj.bound_box
#            bpy.context.scene.render.use_border = True
#            bpy.context.scene.render.border_min_x = xmin / \
#                bpy.context.scene.render.resolution_x
#            bpy.context.scene.render.border_max_x = xmax / \
#                bpy.context.scene.render.resolution_x
#            bpy.context.scene.render.border_min_y = ymin / \
#                bpy.context.scene.render.resolution_y
#            bpy.context.scene.render.border_max_y = ymax / \
#                bpy.context.scene.render.resolution_y

            bpy.ops.render.render()

            # 保存
            if tait_bryan:
                pitch = -pitch
                yaw = -yaw
            save_path = os.path.join(
                save_dir, f'{FBX_NO}_p{round(pitch):+04}_y{round(yaw):+04}_r{round(roll):+04}.png')
            with open(os.path.join(save_dir, 'a.txt'), 'w') as f:
                f.write(f"{np.array(bpy.data.images['Render Result'].pixels)}")
            bpy.data.images['Render Result'].save_render(filepath=save_path)

            with open(save_path.replace('.png', '.json'), 'w') as f:
                json.dump({
                    'pitch': pitch,
                    'yaw': yaw,
                    'roll': roll,
                    'location': head_location,
                    'bbox': [xmin, ymin, xmax, ymax]
                }, f)

bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.delete()
