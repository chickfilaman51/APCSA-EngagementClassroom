import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5)

def is_slouching(landmarks):
    nose = landmarks[0]
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
    return abs(nose.y - avg_shoulder_y) < 0.185

def is_hand_raised(landmarks, hand_landmarks):
    if not hand_landmarks or not landmarks:
        return False
    hand = hand_landmarks[0]
    wrist_y = hand.landmark[0].y
    shoulder_y = landmarks[11].y  
    return wrist_y < shoulder_y

def is_head_down(landmarks):
    nose = landmarks[0]
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
    return abs(nose.y - avg_shoulder_y) < 0.05

def process_frame(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    pose_results = pose.process(frame_rgb)
    hands_results = hands.process(frame_rgb)

    score = 0
    status = "Unknown"

    landmarks = []
    if pose_results.pose_landmarks:
        mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = pose_results.pose_landmarks.landmark

        if not is_slouching(landmarks):
            score += 1
        if not is_head_down(landmarks):
            score += 1
        if is_hand_raised(landmarks, hands_results.multi_hand_landmarks):
            score += 2

        if score >= 3:
            status = "High"
        elif score == 2:
            status = "Medium"
        else:
            status = "Low"

    if hands_results.multi_hand_landmarks:
        for hand in hands_results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

    return status, score
