import numpy as np
from mediapipe.python.solutions.pose import PoseLandmark

def calculate_angle(a, b, c):
    ba = np.subtract(a, b)
    bc = np.subtract(c, b)
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba == 0 or norm_bc == 0:
        return 0.0

    cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    return np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))

def get_angles(landmarks, mp_pose=None):  # можно оставить mp_pose, если вдруг пригодится
    def point(p):  # avoid repeating [x, y]
        return [p.x, p.y]

    lms = PoseLandmark  # <-- используем напрямую импортированный enum
    points = {name: point(landmarks[getattr(lms, name).value]) for name in (
        "LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE", "LEFT_FOOT_INDEX",
        "RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE", "RIGHT_FOOT_INDEX"
    )}

    return {
        "knee_l": calculate_angle(points["LEFT_HIP"], points["LEFT_KNEE"], points["LEFT_ANKLE"]),
        "knee_r": calculate_angle(points["RIGHT_HIP"], points["RIGHT_KNEE"], points["RIGHT_ANKLE"]),
        "ankle_l": calculate_angle(points["LEFT_KNEE"], points["LEFT_ANKLE"], points["LEFT_FOOT_INDEX"]),
        "ankle_r": calculate_angle(points["RIGHT_KNEE"], points["RIGHT_ANKLE"], points["RIGHT_FOOT_INDEX"]),
        "hip_l": calculate_angle(points["LEFT_KNEE"], points["LEFT_HIP"], [points["LEFT_HIP"][0], points["LEFT_HIP"][1] - 0.1]),
        "hip_r": calculate_angle(points["RIGHT_KNEE"], points["RIGHT_HIP"], [points["RIGHT_HIP"][0], points["RIGHT_HIP"][1] - 0.1])
    }
