from ultralytics import YOLO
if __name__ == '__main__':
    # 加载模型   xanylabeling
    #  model = YOLO("yolo26n.pt")
    #  model = YOLO(r"D:\djj\gamecv\runs\detect\train2\weights\last.pt")
    model = YOLO("yolo26s.pt")
    # 训练模型
    results = model.train(data="wheat.yaml",
                          epochs=30,
                          imgsz=640,
                          device="cpu")