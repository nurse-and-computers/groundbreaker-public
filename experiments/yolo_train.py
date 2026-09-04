from ultralytics import YOLO

def train():
    model = YOLO("yolov8s.pt")
    model.train(
        data="dataset.yaml",
        epochs=50,
        imgsz=640,
        batch=16,
        device=0,    # CUDA: 0
        amp=True,    # enables automatic mixed precision (fp16 on GPU)
        workers=0,
    )

if __name__ == "__main__":
    train()
