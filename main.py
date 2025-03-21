import cv2
from pose_model import PoseDetector
from angle_calculation import get_angles


pose_detector = PoseDetector()
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = pose_detector.process_frame(frame)
    frame = pose_detector.draw_landmarks(frame, results)

    if results.pose_landmarks:
        angles = get_angles(results.pose_landmarks.landmark, pose_detector.mp_pose)

        for i, (name, angle) in enumerate(angles.items()):
            cv2.putText(frame, f"{name}: {int(angle)}", (50, 50 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (255, 255, 255), 2)

    cv2.imshow("Pose Estimation", frame)

    if cv2.waitKey(1) & 0xFF == ord('z'):
        break

cap.release()
cv2.destroyAllWindows()
