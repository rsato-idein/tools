"""
https://github.com/Ascend-Research/HeadPoseEstimation-WHENet/blob/master/prepare_images.py
"""
import json
import os

import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
from utils import (align, get_sphere, inverse_rotate_zyx, projectPoints,
                   reference_head, select_euler)

model_points, _ = reference_head(scale=1, pyr=(0., 0., 0.))
kp_idx = np.asarray([17, 21, 26, 22, 45, 42, 39, 36, 35, 31, 54, 48, 57, 8])
kp_idx_model = np.asarray([38, 34, 33, 29, 13, 17, 25, 21, 54, 50, 43, 39, 45, 6])
sphere = []
for theta in range(0, 360, 10):
    for phi in range(0, 180, 10):
        sphere.append(get_sphere(theta, phi, 22))
sphere = np.asarray(sphere)
sphere = sphere + [0, 5, -5]
sphere = sphere.T


def last_8chars(x):
    x = x[-12:]
    x = x.split(".")[0]
    # print(x)
    return (x)


without_top = [0, 3, 5, 8, 9, 11, 12, 14, 15, 16, 18, 20, 21, 22, 23, 24, 25, 26, 27, 29]


def save_img_head(frame, save_path, seq, cam, cam_id, json_file, frame_id):
    img_path = os.path.join(save_path, seq)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = Image.fromarray(frame)
    # print(frame.size)
    E_ref = np.mat([[1, 0, 0, 0.],
                    [0, -1, 0, 0],
                    [0, 0, -1, 50],
                    [0, 0, 0,  1]])
    cam['K'] = np.mat(cam['K'])
    cam['distCoef'] = np.array(cam['distCoef'])
    cam['R'] = np.mat(cam['R'])
    cam['t'] = np.array(cam['t']).reshape((3, 1))
    with open(json_file) as dfile:
        fframe = json.load(dfile)
        count_face = -1
    for face in fframe['people']:
        # 3D Face has 70 3D joints, stored as an array [x1,y1,z1,x2,y2,z2,...]
        face3d = np.array(face['face70']['landmarks']).reshape((-1, 3)).transpose()
        face_conf = np.asarray(face['face70']['averageScore'])
        model_points_3D = np.ones((4, 58), dtype=np.float32)
        model_points_3D[0:3] = model_points
        clean_match = (face_conf[kp_idx] > 0.7)  # only pick points confidence higher than 0.1
        kp_idx_clean = kp_idx[clean_match]
        kp_idx_model_clean = kp_idx_model[clean_match]
        if (len(kp_idx_clean) > 10):
            count_face += 1
            rotation, translation, error, scale = align(np.mat(model_points_3D[0:3, kp_idx_model_clean]),
                                                        np.mat(face3d[:, kp_idx_clean]))
            sphere_new = 0.8 * scale * rotation @ (sphere) + translation
            pt_helmet = projectPoints(sphere_new,
                                      cam['K'], cam['R'], cam['t'],
                                      cam['distCoef'])
            pt_face = projectPoints(face3d,
                                    cam['K'], cam['R'], cam['t'],
                                    cam['distCoef'])
            temp = np.zeros((4, 4))
            temp[0:3, 0:3] = rotation
            temp[0:3, 3:4] = translation
            temp[3, 3] = 1
            E_virt = np.linalg.inv(temp @ np.linalg.inv(E_ref))
            E_real = np.zeros((4, 4))
            E_real[0:3, 0:3] = cam['R']
            E_real[0:3, 3:4] = cam['t']
            E_real[3, 3] = 1

            compound = E_real @ np.linalg.inv(E_virt)
            status, [pitch, yaw, roll] = select_euler(np.rad2deg(inverse_rotate_zyx(compound)))
            yaw = -yaw
            roll = -roll
            if status:
                x_min = int(min(pt_helmet[0, :]))
                y_min = int(min(pt_helmet[1, :]))
                x_max = int(max(pt_helmet[0, :]))
                y_max = int(max(pt_helmet[1, :]))
                if 0 < x_min and 0 < y_min and x_max < frame.size[0] and y_max < frame.size[1]:
                    img = frame.crop((x_min, y_min, x_max, y_max))
                    pt_face_2d = pt_face[:2] - np.array([[x_min], [y_min]])
                    filename = '{0:02d}_{1:01d}_{2:08d}.jpg'.format(cam_id, count_face, frame_id)
                    if not (os.path.exists(img_path)):
                        os.mkdir(img_path)
                    file_path = os.path.join(img_path, filename)
                    img.save(file_path, "JPEG")
                    anno_path = file_path.replace('.jpg', '.json')
                    with open(anno_path, 'w') as f:
                        json.dump({'pitch': pitch, 'yaw': yaw, 'roll': roll, 'landmarks': pt_face_2d.tolist()}, f)


def mtc_dataset(root_path, sequence_name, save_path):
    img_path = os.path.join(root_path, 'hdImgs', sequence_name)
    json_path = os.path.join(root_path, 'hdAnnos', sequence_name, 'hdFace3d')
    img_dir_list = os.listdir(img_path)
    img_dir_list = sorted(img_dir_list, key=last_8chars)

    file_list = os.listdir(json_path)
    json_list = []
    for filename in sorted(file_list, key=last_8chars):
        json_list.append(os.path.join(json_path, filename))
    start_frame = int(json_list[0][-12:].split(".")[0])
    # temp = json_list[-1][-12:]
    # end_frame = int(json_list[-1][-12:].split(".")[0])

    with open(root_path+'/hdAnnos/'+sequence_name+'/calibration_{0}.json'.format(sequence_name)) as cfile:
        calib = json.load(cfile)
    # Cameras are identified by a tuple of (panel#,node#)
    cameras = {(cam['panel'], cam['node']): cam for cam in calib['cameras']}

    for cam_n in tqdm(range(0, 31), leave=False):
        for i in tqdm(range(1, len(img_dir_list)), leave=False):
            curr_dir = os.path.join(img_path, img_dir_list[i])
            # print(os.listdir(curr_dir))
            frame_id = int(img_dir_list[i])
            frame_file_name = "00_{0:02d}_{1:08d}.jpg".format(cam_n, frame_id)
            # print(frame_file_name)
            frame_file_path = os.path.join(curr_dir, frame_file_name)
            if (os.path.isfile(frame_file_path)):
                frame = cv2.imread(os.path.join(frame_file_path))
                save_img_head(frame, save_path, sequence_name, cameras[(0, cam_n)], cam_n, json_list[frame_id - start_frame], frame_id)


if __name__ == '__main__':
    root = '/data/a4_release'
    out_path = os.path.dirname(os.path.abspath(__file__))+'/data/pre_process'
    os.makedirs(out_path, exist_ok=True)

    do_mtc = True

    if do_mtc:
        seq_list = ['171026_pose1', '171026_pose2', '171026_pose3', '171204_pose1', '171204_pose2', '171204_pose3', '171204_pose4', '171204_pose5', '171204_pose6']
        for i in tqdm(range(9)):
            # train: 310889
            # val: 6380
            mtc_dataset(root, seq_list[i], out_path)
    # else:
    #     vid_seq_list = ['170404_haggling_a1', '170404_haggling_a2', '170404_haggling_a3', '170404_haggling_b1', '170404_haggling_b2', '170404_haggling_b3',
    #                     '170407_haggling_a1', '170407_haggling_a2', '170407_haggling_a3', '170407_haggling_b1', '170407_haggling_b2', '170407_haggling_b3']
    #     for i in range(0, 8):
    #         os.makedirs(out_path + '/' + vid_seq_list[i], exist_ok=True)
    #         sample_video(root, vid_seq_list[i], out_path, interval=10)
