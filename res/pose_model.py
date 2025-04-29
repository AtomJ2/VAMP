import cv2
import mediapipe as mp

class PoseDetector:
    def __init__(self):
        self.pose = mp.solutions.pose.Pose()
        self.draw_landmarks_fn = mp.solutions.drawing_utils.draw_landmarks
        self.connections = mp.solutions.pose.POSE_CONNECTIONS

    def process_frame(self, frame):
        return self.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def draw_landmarks(self, frame, results):
        if results.pose_landmarks:
            self.draw_landmarks_fn(frame, results.pose_landmarks, self.connections)
        return frame
