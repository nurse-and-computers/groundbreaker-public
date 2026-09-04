import cv2
from ultralytics import YOLO
import os

# Load your trained YOLO model
model = YOLO("../runs/detect/train6/weights/best.pt")

# Open video
cap = cv2.VideoCapture("video_kitchentoilet.mp4")

# Folder to save best detections
os.makedirs("unique_best", exist_ok=True)

# Track best confidence per class
best_conf = {name: -1 for name in model.names.values()}
best_frames = {}

frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    results = model(frame, conf=0.3)  # run YOLO

    for box in results[0].boxes:
        cls_id = int(box.cls[0].item())
        cls_name = model.names[cls_id]
        conf = float(box.conf[0].item())

        # Check if this detection is better than previous best
        if conf > best_conf[cls_name]:
            # Save annotated frame with bounding boxes
            annotated_frame = results[0].plot()

            best_conf[cls_name] = conf
            best_frames[cls_name] = (annotated_frame.copy(), frame_count, conf)

cap.release()

# Save best detections per class
for cls_name, (frame, frame_num, conf) in best_frames.items():
    out_path = f"unique_best/{cls_name}_frame{frame_num}_conf{conf:.2f}.jpg"
    cv2.imwrite(out_path, frame)
    print(f"✅ Saved best {cls_name} at frame {frame_num} with conf {conf:.2f}")
