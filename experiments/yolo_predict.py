from ultralytics import YOLO

# Load your trained model
model = YOLO("../runs/detect/train6/weights/best.pt")

# Run inference on a video
results = model.predict(
    source="video_bedroom.mp4",   # path to your video file
    conf=0.5,                           # confidence threshold
    save=True,                          # save output video with bounding boxes
    show=True                           # display video while processing
)