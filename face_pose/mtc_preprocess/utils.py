"""
https://github.com/Ascend-Research/HeadPoseEstimation-WHENet/blob/master/utils.py
"""

from math import cos, pi, sin

import numpy as np
from scipy.spatial import Delaunay


def projectPoints(X, K, R, t, Kd):
    """ Projects points X (3xN) using camera intrinsics K (3x3),
    extrinsics (R,t) and distortion parameters Kd=[k1,k2,p1,p2,k3].
    Roughly, x = K*(R*X + t) + distortion
    See http://docs.opencv.org/2.4/doc/tutorials/calib3d/camera_calibration/camera_calibration.html
    or cv2.projectPoints
    """

    x = np.asarray(R * X + t)

    x[0:2, :] = x[0:2, :] / x[2, :]

    r = x[0, :] * x[0, :] + x[1, :] * x[1, :]

    x[0, :] = x[0, :] * (1 + Kd[0] * r + Kd[1] * r * r + Kd[4] * r * r * r) + 2 * Kd[2] * x[0, :] * x[1, :] + Kd[3] * (
        r + 2 * x[0, :] * x[0, :])
    x[1, :] = x[1, :] * (1 + Kd[0] * r + Kd[1] * r * r + Kd[4] * r * r * r) + 2 * Kd[3] * x[0, :] * x[1, :] + Kd[2] * (
        r + 2 * x[1, :] * x[1, :])

    x[0, :] = K[0, 0] * x[0, :] + K[0, 1] * x[1, :] + K[0, 2]
    x[1, :] = K[1, 0] * x[0, :] + K[1, 1] * x[1, :] + K[1, 2]

    return x


def align(model, data):
    """Align two trajectories using the method of Horn (closed-form).
    https://github.com/raulmur/evaluate_ate_scale
    Input:
    model -- first trajectory (3xn)
    data -- second trajectory (3xn)
    Output:
    rot -- rotation matrix (3x3)
    trans -- translation vector (3x1)
    trans_error -- translational error per point (1xn)
    """
    np.set_printoptions(precision=3, suppress=True)
    model_zerocentered = model - model.mean(1)
    data_zerocentered = data - data.mean(1)

    W = np.zeros((3, 3))
    for column in range(model.shape[1]):
        W += np.outer(model_zerocentered[:, column], data_zerocentered[:, column])
    U, d, Vh = np.linalg.linalg.svd(W.transpose())
    S = np.matrix(np.identity(3))
    if (np.linalg.det(U) * np.linalg.det(Vh) < 0):
        S[2, 2] = -1
    rot = U * S * Vh

    rotmodel = rot * model_zerocentered
    dots = 0.0
    norms = 0.0

    for column in range(data_zerocentered.shape[1]):
        dots += np.dot(data_zerocentered[:, column].transpose(), rotmodel[:, column])
        normi = np.linalg.norm(model_zerocentered[:, column])
        norms += normi * normi

    s = float(dots / norms)

    trans = data.mean(1) - s * rot * model.mean(1)

    model_aligned = s * rot * model + trans
    alignment_error = model_aligned - data

    trans_error = np.sqrt(np.sum(np.multiply(alignment_error, alignment_error), 0)).A[0]

    return rot, trans, trans_error, s


def reference_head(scale=0.01, pyr=(10., 0.0, 0.0)):
    kps = np.asarray([[-7.308957, 0.913869, 0.000000], [-6.775290, -0.730814, -0.012799],
                      [-5.665918, -3.286078, 1.022951], [-5.011779, -4.876396, 1.047961],
                      [-4.056931, -5.947019, 1.636229], [-1.833492, -7.056977, 4.061275],
                      [0.000000, -7.415691, 4.070434], [1.833492, -7.056977, 4.061275],
                      [4.056931, -5.947019, 1.636229], [5.011779, -4.876396, 1.047961],
                      [5.665918, -3.286078, 1.022951],
                      [6.775290, -0.730814, -0.012799], [7.308957, 0.913869, 0.000000],
                      [5.311432, 5.485328, 3.987654], [4.461908, 6.189018, 5.594410],
                      [3.550622, 6.185143, 5.712299], [2.542231, 5.862829, 4.687939],
                      [1.789930, 5.393625, 4.413414], [2.693583, 5.018237, 5.072837],
                      [3.530191, 4.981603, 4.937805], [4.490323, 5.186498, 4.694397],
                      [-5.311432, 5.485328, 3.987654], [-4.461908, 6.189018, 5.594410],
                      [-3.550622, 6.185143, 5.712299], [-2.542231, 5.862829, 4.687939],
                      [-1.789930, 5.393625, 4.413414], [-2.693583, 5.018237, 5.072837],
                      [-3.530191, 4.981603, 4.937805], [-4.490323, 5.186498, 4.694397],
                      [1.330353, 7.122144, 6.903745], [2.533424, 7.878085, 7.451034],
                      [4.861131, 7.878672, 6.601275], [6.137002, 7.271266, 5.200823],
                      [6.825897, 6.760612, 4.402142], [-1.330353, 7.122144, 6.903745],
                      [-2.533424, 7.878085, 7.451034], [-4.861131, 7.878672, 6.601275],
                      [-6.137002, 7.271266, 5.200823], [-6.825897, 6.760612, 4.402142],
                      [-2.774015, -2.080775, 5.048531], [-0.509714, -1.571179, 6.566167],
                      [0.000000, -1.646444, 6.704956], [0.509714, -1.571179, 6.566167],
                      [2.774015, -2.080775, 5.048531], [0.589441, -2.958597, 6.109526],
                      [0.000000, -3.116408, 6.097667], [-0.589441, -2.958597, 6.109526],
                      [-0.981972, 4.554081, 6.301271], [-0.973987, 1.916389, 7.654050],
                      [-2.005628, 1.409845, 6.165652], [-1.930245, 0.424351, 5.914376],
                      [-0.746313, 0.348381, 6.263227], [0.000000, 0.000000, 6.763430],
                      [0.746313, 0.348381, 6.263227], [1.930245, 0.424351, 5.914376],
                      [2.005628, 1.409845, 6.165652], [0.973987, 1.916389, 7.654050],
                      [0.981972, 4.554081, 6.301271]]).T
    R = rotate_zyx(np.deg2rad(pyr))
    kps = transform(R, kps*scale)
    tris = Delaunay(kps[:2].T).simplices.copy()
    return kps, tris


def rotate_zyx(theta):
    sx, sy, sz = np.sin(theta)
    cx, cy, cz = np.cos(theta)
    return np.array([
        [cy * cz, cy * sz, -sy, 0],
        [-cx * sz + cz * sx * sy, cx * cz + sx * sy * sz, cy * sx, 0],
        [cx * cz * sy + sx * sz, cx * sy * sz - cz * sx, cx * cy, 0],
        [0, 0, 0, 1]], dtype=float)


def transform(E, p):
    p = np.array(p)
    if p.ndim > 1:
        return E[:3, :3]@p + E[:3, 3, None]
    return E[:3, :3]@p + E[:3, 3]


def get_sphere(theta, phi, row):
    theta = theta / 180. * pi
    phi = phi / 180. * pi
    x = row * cos(theta) * sin(phi)
    y = row * sin(theta) * sin(phi)
    z = row * cos(phi)
    return x, y, z


def select_euler(two_sets):
    pitch, yaw, roll = two_sets[0]
    pitch2, yaw2, roll2 = two_sets[1]
    if abs(roll) < 90 and abs(pitch) < 90:
        return True, [pitch, yaw, roll]
    elif abs(roll2) < 90 and abs(pitch2) < 90:
        return True, [pitch2, yaw2, roll2]
    else:
        return False, [-999, -999, -999]


def inverse_rotate_zyx(M):
    if np.linalg.norm(M[:3, :3].T @ M[:3, :3] - np.eye(3)) > 1e-5:
        raise ValueError('Matrix is not a rotation')

    # no gimbal lock
    eps = 1e-7
    y0 = np.clip(np.arcsin(-M[0, 2]), -np.pi/2 + eps, np.pi/2 - eps)
    if y0 >= 0:
        y1 = -y0 + np.pi
    else:
        y1 = -y0 - np.pi
    cy0 = np.cos(y0)
    cy1 = np.cos(y1)

    x0 = np.arctan2(M[1, 2] / cy0, M[2, 2] / cy0)
    x1 = np.arctan2(M[1, 2] / cy1, M[2, 2] / cy1)

    z0 = np.arctan2(M[0, 1] / cy0, M[0, 0] / cy0)
    z1 = np.arctan2(M[0, 1] / cy1, M[0, 0] / cy1)
    return np.array((x0, y0, z0)), np.array((x1, y1, z1))
