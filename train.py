from ultralytics import YOLO
if __name__ == '__main__':
    # 加载模型
    model = YOLO("yolov8n.pt")
    # 训练模型
    results = model.train(data="wheat.yaml",
                          epochs=30,
                          imgsz=640,
                          device="cpu")