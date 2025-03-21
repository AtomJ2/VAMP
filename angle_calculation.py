import numpy as np


def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)


def get_angles(landmarks, mp_pose):
    hip_l = [landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP].y]
    knee_l = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y]
    ankle_l = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y]
    foot_l = [landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX].x, landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX].y]

    hip_r = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y]
    knee_r = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y]
    ankle_r = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y]
    foot_r = [landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX].x, landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX].y]

    angles = {
        "knee_l": calculate_angle(hip_l, knee_l, ankle_l),
        "knee_r": calculate_angle(hip_r, knee_r, ankle_r),
        "ankle_l": calculate_angle(knee_l, ankle_l, foot_l),
        "ankle_r": calculate_angle(knee_r, ankle_r, foot_r),
        "hip_l": calculate_angle(knee_l, hip_l, [hip_l[0], hip_l[1] - 0.1]),
        "hip_r": calculate_angle(knee_r, hip_r, [hip_r[0], hip_r[1] - 0.1])
    }

    return angles
