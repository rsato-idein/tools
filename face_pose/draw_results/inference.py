import argparse
import os
import nnoir
import numpy as np
from PIL import Image, ImageDraw


def decode(output, is_6D=False):
    if is_6D:
        x_raw = output[0:3]  # batch*3
        y_raw = output[3:6]  # batch*3

        x = x_raw / max(np.linalg.norm(x_raw), 1e-8)  # batch*3
        z = np.cross(x, y_raw)  # batch*3
        z = z / max(np.linalg.norm(x), 1e-8)  # batch*3
        y = np.cross(z, x)  # batch*3

        x = x.reshape(3, 1)
        y = y.reshape(3, 1)
        z = z.reshape(3, 1)
        matrix = np.concatenate((x, y, z), axis=-1)  # batch*3*3

        R = matrix
        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        singular = sy < 1e-6
        singular = singular.astype(float)

        x = np.arctan2(R[2, 1], R[2, 2])
        y = np.arctan2(-R[2, 0], sy)
        z = np.arctan2(R[1, 0], R[0, 0])

        xs = np.arctan2(-R[1, 2], R[1, 1])
        ys = np.arctan2(-R[2, 0], sy)
        zs = R[1, 0] * 0

        pitch = x * (1 - singular) + xs * singular
        yaw = y * (1 - singular) + ys * singular
        roll = z * (1 - singular) + zs * singular

    else:
        q0, q1, q2, q3, *_ = output
        pitch = np.arctan(2 * (q0 * q1 + q2 * q3) / (1 - 2 * (q1 * q1 + q2 * q2)))
        yaw = np.arcsin(2 * (q0 * q2 - q3 * q1))
        roll = np.arctan(2 * (q0 * q3 + q1 * q2) / (1 - 2 * (q2 * q2 + q3 * q3)))

    return np.rad2deg([pitch, yaw, roll])


def draw_axis(img, yaw, pitch, roll, tdx=None, tdy=None, size=100):

    pitch = pitch * np.pi / 180
    yaw = -(yaw * np.pi / 180)
    roll = roll * np.pi / 180

    # X-Axis pointing to right. drawn in red
    x1 = size * (np.cos(yaw) * np.cos(roll)) + tdx
    y1 = size * (np.cos(pitch) * np.sin(roll) + np.cos(roll) * np.sin(pitch) * np.sin(yaw)) + tdy

    # Y-Axis | drawn in green
    #        v
    x2 = size * (-np.cos(yaw) * np.sin(roll)) + tdx
    y2 = size * (np.cos(pitch) * np.cos(roll) - np.sin(pitch) * np.sin(yaw) * np.sin(roll)) + tdy

    # Z-Axis (out of the screen) drawn in blue
    x3 = size * (np.sin(yaw)) + tdx
    y3 = size * (-np.cos(yaw) * np.sin(pitch)) + tdy

    draw = ImageDraw.Draw(img)
    draw.line((int(tdx), int(tdy), int(x1), int(y1)), fill=(0, 0, 255), width=4)
    draw.line((int(tdx), int(tdy), int(x2), int(y2)), fill=(0, 255, 0), width=4)
    draw.line((int(tdx), int(tdy), int(x3), int(y3)), fill=(255, 0, 0), width=4)

    return img


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('nnoir_path_list', type=str, nargs="*")
    parser.add_argument('image_dir', type=str)
    args = parser.parse_args()

    n_models = {os.path.basename(nnoir_path): nnoir.load(nnoir_path) for nnoir_path in args.nnoir_path_list}

    inferenced_images = []
    for i in range(1, 301):
        image = Image.open(os.path.join(args.image_dir, f'{i:03}.jpg'))
        inputs = image.crop((460, 0, 820, 360)).resize((96, 96))
        inputs = np.asarray(inputs).reshape(1, 96, 96, 3).transpose(0, 3, 1, 2).astype(np.float32)
        inputs /= 255
        aligned_image = Image.new('RGB', (128*4, 128))
        for i, (n_name, n_model) in enumerate(n_models.items()):
            outputs, = n_model.run(inputs)
            pitch, yaw, roll = decode(outputs[0], is_6D='6' in n_name)
            each_image = draw_axis(image.copy(), pitch=pitch, yaw=yaw, roll=roll, tdx=640, tdy=180)
            each_image = each_image.crop((460, 0, 820, 360)).resize((128, 128))
            aligned_image.paste(each_image, (i * 128, 0))
        inferenced_images.append(aligned_image)
    inferenced_images[0].save('all.gif', save_all=True, append_images=inferenced_images[1:], loop=0)
