from ultralytics import YOLO

# 1. 加载你训练好的模型 (注意路径，通常在 weights/best.pt)
model = YOLO(r"D:\djj\gamecv\runs\detect\train2\weights\best.pt")

# 2. 对单张图片进行预测
results = model.predict(source=r"D:\djj\gamecv\data\test", save=True, conf=0.5)

# 3. 打印结果
for result in results:
    print(result.boxes)  # 打印框的坐标、置信度和类别