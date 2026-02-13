from ultralytics import YOLO
if __name__ == '__main__':
    # 加载模型   xanylabeling
    model = YOLO(r"D:\djj\gamecv\runs\detect\train2\weights\last.pt")
    # 训练模型
    results = model.train(data="wheat.yaml",
                          epochs=50,
                          imgsz=640,
                          device="cpu")